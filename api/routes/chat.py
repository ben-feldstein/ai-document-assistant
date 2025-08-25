"""Chat routes for text-based queries and responses."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.models.db import get_db
from api.models.entities import User
from api.models.schemas import ChatRequest, ChatResponse, ResponseEnvelope
from api.routes.auth import get_current_user
from api.services.orchestrator import orchestrator_service
from api.services.rate_limit import rate_limit_service

router = APIRouter()


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Chat endpoint for text-based queries.
    
    This endpoint processes text queries and returns AI-generated responses
    based on the policy corpus.
    """
    try:
        # If org_id is not provided, get it from user's primary organization
        if not request.org_id:
            # Get user's primary organization (first one they belong to)
            from api.models.entities import Membership
            membership = db.query(Membership).filter(
                Membership.user_id == current_user.id
            ).first()
            
            if membership:
                request.org_id = membership.org_id
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User is not a member of any organization"
                )
        
        # Set user_id if not provided
        if not request.user_id:
            request.user_id = current_user.id
        
        # Check rate limits
        allowed, remaining, reset_time = await rate_limit_service.check_rate_limit(
            request.org_id, 
            request.user_id
        )
        
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Try again in {reset_time} seconds.",
                headers={"X-RateLimit-Reset": str(reset_time)}
            )
        
        # Record the request
        await rate_limit_service.record_request(request.org_id, request.user_id)
        
        # Process the query through the orchestrator
        response = await orchestrator_service.handle_text_query(request)
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing your request: {str(e)}"
        )


@router.get("/history")
async def get_chat_history(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get chat history for the current user.
    
    This endpoint returns a paginated list of previous chat interactions.
    """
    try:
        from api.models.entities import QueryLog, Membership
        
        # Get user's organizations
        memberships = db.query(Membership).filter(
            Membership.user_id == current_user.id
        ).all()
        
        org_ids = [m.org_id for m in memberships]
        
        if not org_ids:
            return {
                "ok": True,
                "data": [],
                "total": 0
            }
        
        # Query chat history
        from sqlalchemy import desc
        query_logs = db.query(QueryLog).filter(
            QueryLog.org_id.in_(org_ids),
            QueryLog.user_id == current_user.id
        ).order_by(desc(QueryLog.created_at)).offset(offset).limit(limit).all()
        
        # Format response
        history = []
        for log in query_logs:
            history.append({
                "id": log.id,
                "input": log.input_text,
                "tokens_in": log.tokens_in,
                "tokens_out": log.tokens_out,
                "vendor": log.vendor,
                "cached": log.cached,
                "latency_ms": log.latency_ms,
                "error": log.error,
                "created_at": log.created_at.isoformat()
            })
        
        # Get total count
        total = db.query(QueryLog).filter(
            QueryLog.org_id.in_(org_ids),
            QueryLog.user_id == current_user.id
        ).count()
        
        return {
            "ok": True,
            "data": history,
            "total": total,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching chat history: {str(e)}"
        )


@router.get("/stats")
async def get_chat_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get chat statistics for the current user.
    
    This endpoint returns aggregated statistics about the user's chat usage.
    """
    try:
        from api.models.entities import QueryLog, Membership
        from sqlalchemy import func
        
        # Get user's organizations
        memberships = db.query(Membership).filter(
            Membership.user_id == current_user.id
        ).all()
        
        org_ids = [m.org_id for m in memberships]
        
        if not org_ids:
            return {
                "ok": True,
                "data": {
                    "total_queries": 0,
                    "total_tokens_in": 0,
                    "total_tokens_out": 0,
                    "avg_latency_ms": 0,
                    "cache_hit_rate": 0,
                    "error_rate": 0
                }
            }
        
        # Calculate statistics - simplified to avoid SQLAlchemy version issues
        total_queries = db.query(func.count(QueryLog.id)).filter(
            QueryLog.org_id.in_(org_ids),
            QueryLog.user_id == current_user.id
        ).scalar() or 0
        
        total_tokens_in = db.query(func.sum(QueryLog.tokens_in)).filter(
            QueryLog.org_id.in_(org_ids),
            QueryLog.user_id == current_user.id
        ).scalar() or 0
        
        total_tokens_out = db.query(func.sum(QueryLog.tokens_out)).filter(
            QueryLog.org_id.in_(org_ids),
            QueryLog.user_id == current_user.id
        ).scalar() or 0
        
        avg_latency = db.query(func.avg(QueryLog.latency_ms)).filter(
            QueryLog.org_id.in_(org_ids),
            QueryLog.user_id == current_user.id
        ).scalar() or 0
        
        # Count cached queries
        cached_count = db.query(func.count(QueryLog.id)).filter(
            QueryLog.org_id.in_(org_ids),
            QueryLog.user_id == current_user.id,
            QueryLog.cached == True
        ).scalar() or 0
        
        # Count error queries
        error_count = db.query(func.count(QueryLog.id)).filter(
            QueryLog.org_id.in_(org_ids),
            QueryLog.user_id == current_user.id,
            QueryLog.error.isnot(None)
        ).scalar() or 0
        
        cache_hit_rate = (cached_count / total_queries * 100) if total_queries > 0 else 0
        error_rate = (error_count / total_queries * 100) if total_queries > 0 else 0
        
        return {
            "ok": True,
            "data": {
                "total_queries": total_queries,
                "total_tokens_in": total_tokens_in,
                "total_tokens_out": total_tokens_out,
                "avg_latency_ms": round(avg_latency, 2),
                "cache_hit_rate": round(cache_hit_rate, 2),
                "error_rate": round(error_rate, 2)
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching chat statistics: {str(e)}"
        )


@router.delete("/history/{query_id}")
async def delete_chat_history_item(
    query_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a specific chat history item.
    
    This endpoint allows users to remove individual chat interactions from their history.
    """
    try:
        from api.models.entities import QueryLog, Membership
        
        # Get user's organizations
        memberships = db.query(Membership).filter(
            Membership.user_id == current_user.id
        ).all()
        
        org_ids = [m.org_id for m in memberships]
        
        # Find and delete the query log
        query_log = db.query(QueryLog).filter(
            QueryLog.id == query_id,
            QueryLog.org_id.in_(org_ids),
            QueryLog.user_id == current_user.id
        ).first()
        
        if not query_log:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat history item not found"
            )
        
        db.delete(query_log)
        db.commit()
        
        return {
            "ok": True,
            "data": {"message": "Chat history item deleted successfully"}
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while deleting chat history item: {str(e)}"
        )
