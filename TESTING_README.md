# 🧪 Testing Your AI Document Assistant

This directory contains two comprehensive testing tools to validate all your API functionality before building the modern UI.

## 🎯 **What We're Testing**

- ✅ **System Health** - All services running properly
- 🔐 **Authentication** - User registration, login, JWT tokens
- 💬 **Chat Interface** - AI-powered policy queries
- 🎤 **Voice Interface** - WebSocket audio processing
- 📚 **Document Management** - Upload, search, and retrieval
- ⚙️ **Admin Features** - System monitoring and management
- 📊 **Metrics** - Prometheus monitoring integration
- 🚦 **Rate Limiting** - API protection mechanisms

## 🖥️ **Option 1: Interactive HTML UI (Recommended for Manual Testing)**

### **Quick Start**
1. **Open the file**: `test-ui.html` in your web browser
2. **Check system health**: Click "Check System Health" on the Overview tab
3. **Test authentication**: Go to Auth tab, register/login with test credentials
4. **Try chat**: Go to Chat tab, send messages once authenticated
5. **Test voice**: Go to Voice tab, connect WebSocket and try recording
6. **Upload documents**: Go to Corpus tab, upload and search documents
7. **Check admin**: Go to Admin tab, view system metrics and logs

### **Features**
- **Tabbed interface** for organized testing
- **Real-time results** with color-coded success/error indicators
- **Interactive forms** for all API endpoints
- **WebSocket testing** for voice features
- **JWT token management** for authentication testing

## 🐍 **Option 2: Automated Python Testing Script**

### **Quick Start**
1. **Install dependencies**:
   ```bash
   pip install -r test-requirements.txt
   ```

2. **Run the test suite**:
   ```bash
   python test_api.py
   ```

3. **Review results**: The script will show detailed pass/fail results for each test

### **What It Tests Automatically**
- System health and service status
- All API endpoints systematically
- Authentication flow (register → login → use)
- Chat functionality with sample messages
- Document upload, search, and listing
- WebSocket connection testing
- Rate limiting validation
- Admin endpoint accessibility

## 🚀 **Testing Workflow**

### **Phase 1: Basic Validation**
1. Run the Python test script to get a quick overview
2. Fix any critical failures
3. Use the HTML UI to manually verify working features

### **Phase 2: Feature Testing**
1. Test each major feature systematically
2. Document any issues or unexpected behavior
3. Validate error handling and edge cases

### **Phase 3: Integration Testing**
1. Test complete user workflows
2. Verify data flows between services
3. Check performance under load

## 🔧 **Troubleshooting Common Issues**

### **"Connection Refused" Errors**
- Make sure all services are running: `docker-compose -f infra/docker-compose.yml up -d`
- Check service health: `docker-compose -f infra/docker-compose.yml ps`

### **Authentication Failures**
- Verify the auth service is healthy in the health check
- Check that the database is accessible
- Ensure JWT secret is properly configured

### **WebSocket Connection Issues**
- Verify the WebSocket endpoint is accessible
- Check browser console for connection errors
- Ensure the voice service is running

### **Document Upload Failures**
- Check that the vectorizer service is healthy
- Verify database connectivity
- Check file size and format limits

## 📊 **Expected Test Results**

### **All Tests Should Pass**
- ✅ Health Check: All services healthy
- ✅ Authentication: User registration and login
- ✅ Chat: Message sending and AI responses
- ✅ Voice: WebSocket connection and audio handling
- ✅ Documents: Upload, search, and retrieval
- ✅ Admin: System metrics and user statistics

### **If Tests Fail**
1. **Check service logs**: `docker-compose -f infra/docker-compose.yml logs [service-name]`
2. **Verify configuration**: Check environment variables and service settings
3. **Test individual endpoints**: Use the HTML UI to isolate issues
4. **Check dependencies**: Ensure all required services are running

## 🎯 **Next Steps After Testing**

### **All Tests Pass** 🎉
- Your API is working perfectly!
- Start building the modern UI with confidence
- Consider adding more comprehensive test coverage

### **Some Tests Fail** 🔧
- Fix the failing functionality first
- Re-run tests to verify fixes
- Document any workarounds or limitations

### **Many Tests Fail** 🚨
- Review service configuration
- Check Docker container health
- Verify all dependencies are properly installed

## 🌟 **Pro Tips**

1. **Start with the Python script** for a quick overview
2. **Use the HTML UI** for interactive debugging
3. **Check the Grafana dashboard** for system metrics
4. **Monitor Docker logs** for detailed error information
5. **Test one feature at a time** to isolate issues

## 📝 **Customizing Tests**

### **Modify Test Data**
- Edit `test_api.py` to change test messages, documents, etc.
- Update `test-ui.html` to modify default form values

### **Add New Tests**
- Extend the `APITester` class in `test_api.py`
- Add new tabs/features to `test-ui.html`

### **Change Test Configuration**
- Modify `BASE_URL` and `WS_URL` in `test_api.py`
- Update endpoint paths if your API structure changes

---

**Happy Testing! 🚀** Once all tests pass, you'll have a rock-solid foundation for building your modern UI.
