"""Admin routes for system administration and configuration."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from api.models.db import get_db
from api.models.entities import User, Org, Membership, RateLimit, FeatureFlag, Doc, Embedding
from api.models.schemas import RateLimitUpdate, FeatureFlagUpdate
from api.routes.auth import get_current_user
from api.services.rate_limit import rate_limit_service
from api.services.orchestrator import orchestrator_service

router = APIRouter()


async def require_admin_role(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    org_id: Optional[int] = None
) -> tuple[User, Session, int]:
    """Dependency to require admin or owner role."""
    # Get user's organizations
    memberships = db.query(Membership).filter(
        Membership.user_id == current_user.id
    ).all()
    
    if not memberships:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a member of any organization"
        )
    
    # If org_id is specified, check access to that org
    if org_id:
        membership = db.query(Membership).filter(
            Membership.org_id == org_id,
            Membership.user_id == current_user.id
        ).first()
        
        if not membership or membership.role not in ["admin", "owner"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions for this organization"
            )
        
        return current_user, db, org_id
    
    # Otherwise, return the first org where user has admin/owner role
    for membership in memberships:
        if membership.role in ["admin", "owner"]:
            return current_user, db, membership.org_id
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="User does not have admin permissions in any organization"
    )


@router.post("/rate-limits")
async def update_rate_limits(
    rate_limit: RateLimitUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update rate limits for an organization."""
    try:
        # Verify user has admin/owner role
        membership = db.query(Membership).filter(
            Membership.org_id == rate_limit.org_id,
            Membership.user_id == current_user.id
        ).first()
        
        if not membership or membership.role not in ["admin", "owner"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to update rate limits"
            )
        
        # Update rate limits in the service
        success = await rate_limit_service.set_org_rate_limits(
            rate_limit.org_id,
            rate_limit.rpm,
            rate_limit.burst
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update rate limits"
            )
        
        # Update database record
        existing_limit = db.query(RateLimit).filter(
            RateLimit.org_id == rate_limit.org_id
        ).first()
        
        if existing_limit:
            existing_limit.rpm = rate_limit.rpm
            existing_limit.burst = rate_limit.burst
        else:
            new_limit = RateLimit(
                org_id=rate_limit.org_id,
                rpm=rate_limit.rpm,
                burst=rate_limit.burst
            )
            db.add(new_limit)
        
        db.commit()
        
        return {
            "ok": True,
            "data": {
                "message": "Rate limits updated successfully",
                "org_id": rate_limit.org_id,
                "rpm": rate_limit.rpm,
                "burst": rate_limit.burst
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating rate limits: {str(e)}"
        )


@router.get("/rate-limits/{org_id}")
async def get_rate_limits(
    org_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get rate limit configuration for an organization."""
    try:
        # Verify user has access to this organization
        membership = db.query(Membership).filter(
            Membership.org_id == org_id,
            Membership.user_id == current_user.id
        ).first()
        
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this organization"
            )
        
        # Get rate limit stats
        stats = await rate_limit_service.get_rate_limit_stats(org_id)
        
        return {
            "ok": True,
            "data": stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting rate limits: {str(e)}"
        )


@router.post("/feature-flags")
async def update_feature_flag(
    feature_flag: FeatureFlagUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a feature flag."""
    try:
        # Verify user has admin/owner role in at least one organization
        membership = db.query(Membership).filter(
            Membership.user_id == current_user.id,
            Membership.role.in_(["admin", "owner"])
        ).first()
        
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to update feature flags"
            )
        
        # Update or create feature flag
        existing_flag = db.query(FeatureFlag).filter(
            FeatureFlag.name == feature_flag.name
        ).first()
        
        if existing_flag:
            existing_flag.enabled = feature_flag.enabled
            if feature_flag.description:
                existing_flag.description = feature_flag.description
        else:
            new_flag = FeatureFlag(
                name=feature_flag.name,
                enabled=feature_flag.enabled,
                description=feature_flag.description
            )
            db.add(new_flag)
        
        db.commit()
        
        return {
            "ok": True,
            "data": {
                "message": "Feature flag updated successfully",
                "name": feature_flag.name,
                "enabled": feature_flag.enabled
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating feature flag: {str(e)}"
        )


@router.get("/feature-flags")
async def list_feature_flags(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all feature flags."""
    try:
        # Verify user has admin/owner role in at least one organization
        membership = db.query(Membership).filter(
            Membership.user_id == current_user.id,
            Membership.role.in_(["admin", "owner"])
        ).first()
        
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to view feature flags"
            )
        
        # Get all feature flags
        flags = db.query(FeatureFlag).all()
        
        return {
            "ok": True,
            "data": [
                {
                    "name": flag.name,
                    "enabled": flag.enabled,
                    "description": flag.description,
                    "created_at": flag.created_at.isoformat(),
                    "updated_at": flag.updated_at.isoformat()
                }
                for flag in flags
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing feature flags: {str(e)}"
        )


@router.get("/system-status")
async def get_system_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get overall system status and health."""
    try:
        # Verify user has admin/owner role in at least one organization
        membership = db.query(Membership).filter(
            Membership.user_id == current_user.id,
            Membership.role.in_(["admin", "owner"])
        ).first()
        
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to view system status"
            )
        
        # Get system status from orchestrator
        system_status = await orchestrator_service.get_system_status()
        
        # Get additional database stats - FILTERED BY USER'S ORGANIZATION
        from sqlalchemy import func
        
        user_org_id = membership.org_id
        
        # Only count users, docs, and embeddings from user's organization
        org_users = db.query(func.count(User.id)).join(Membership).filter(Membership.org_id == user_org_id).scalar()
        org_docs = db.query(func.count(Doc.id)).filter(Doc.org_id == user_org_id).scalar()
        org_embeddings = db.query(func.count(Embedding.id)).join(Doc).filter(Doc.org_id == user_org_id).scalar()
        
        system_status.update({
            "database": {
                "organization_id": user_org_id,
                "organization_users": org_users,
                "organization_documents": org_docs,
                "organization_embeddings": org_embeddings,
                "security_note": "Data filtered to user's organization only"
            }
        })
        
        return {
            "ok": True,
            "data": system_status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting system status: {str(e)}"
        )


@router.post("/cache/clear")
async def clear_cache(
    pattern: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Clear cache entries."""
    try:
        # Verify user has admin/owner role in at least one organization
        membership = db.query(Membership).filter(
            Membership.user_id == current_user.id,
            Membership.role.in_(["admin", "owner"])
        ).first()
        
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to clear cache"
            )
        
        from api.services.cache import cache_service
        
        if pattern:
            # Clear specific pattern
            cleared_count = await cache_service.invalidate_cache(pattern)
            message = f"Cleared {cleared_count} cache entries matching pattern: {pattern}"
        else:
            # Clear all caches
            await cache_service.clear_all_caches()
            message = "All caches cleared successfully"
        
        return {
            "ok": True,
            "data": {"message": message}
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error clearing cache: {str(e)}"
        )


@router.get("/organizations")
async def list_organizations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all organizations (admin only)."""
    try:
        # Verify user has admin/owner role in at least one organization
        membership = db.query(Membership).filter(
            Membership.user_id == current_user.id,
            Membership.role.in_(["admin", "owner"])
        ).first()
        
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to view organizations"
            )
        
        # Get all organizations with member counts
        orgs = db.query(Org).all()
        
        org_data = []
        for org in orgs:
            member_count = db.query(Membership).filter(
                Membership.org_id == org.id
            ).count()
            
            org_data.append({
                "id": org.id,
                "name": org.name,
                "plan": org.plan,
                "member_count": member_count,
                "created_at": org.created_at.isoformat(),
                "updated_at": org.updated_at.isoformat()
            })
        
        return {
            "ok": True,
            "data": org_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing organizations: {str(e)}"
        )
