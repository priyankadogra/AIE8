# Deployment Checklist

Use this checklist to deploy Scout to production.

## Pre-Deployment

### ✅ Local Testing
- [ ] Backend runs locally: `./start_backend.sh`
- [ ] Frontend runs locally: `cd frontend && npm run dev`
- [ ] Can connect to backend from frontend
- [ ] API test passes: `python test_api.py`
- [ ] Chat works with valid OpenAI API key
- [ ] Data preparation works (clicks "🔄 Prepare Data")

### ✅ Code Review
- [ ] All TODO comments addressed
- [ ] No hardcoded API keys in code
- [ ] No sensitive data in repository
- [ ] `.gitignore` properly configured
- [ ] All new files committed to git

## Backend Deployment (Choose One)

### Option A: Vercel
- [ ] Create Vercel account
- [ ] Install Vercel CLI: `npm i -g vercel`
- [ ] Run `vercel` from project root
- [ ] Note the deployed backend URL
- [ ] Test backend: `curl https://your-backend.vercel.app/`

### Option B: Railway
- [ ] Create Railway account
- [ ] Connect GitHub repository
- [ ] Set start command: `uvicorn app.api:app --host 0.0.0.0 --port $PORT`
- [ ] Deploy and note the URL
- [ ] Test backend: `curl https://your-backend.railway.app/`

### ✅ Backend Verification
- [ ] Backend URL is accessible
- [ ] `/` returns health check JSON
- [ ] `/api/health` returns index status
- [ ] CORS is properly configured

## Frontend Deployment (Vercel)

### ✅ Preparation
- [ ] Update API URL in `frontend/app/page.tsx` (or keep dynamic for user config)
- [ ] Test build locally: `cd frontend && npm run build`
- [ ] No build errors

### ✅ Deploy
- [ ] Navigate to frontend: `cd frontend`
- [ ] Run `vercel`
- [ ] Follow prompts
- [ ] Note the deployed frontend URL
- [ ] Test frontend: Open URL in browser

### ✅ Frontend Verification
- [ ] Frontend loads without errors
- [ ] Settings panel opens
- [ ] Can enter API keys
- [ ] Can connect to backend (test with ping)

## Post-Deployment Testing

### ✅ End-to-End Testing
- [ ] Open deployed frontend
- [ ] Enter OpenAI API key in Settings
- [ ] Update API URL if needed (or use default)
- [ ] Click "🔄 Prepare Data"
- [ ] Wait for data preparation (may take 1-2 minutes)
- [ ] Send test message: "What events are happening this week?"
- [ ] Receive response from agent
- [ ] Test with Cohere reranking (if you have key)

### ✅ Performance Check
- [ ] Page loads in < 3 seconds
- [ ] Chat responses arrive in < 10 seconds
- [ ] No console errors in browser
- [ ] Mobile responsive (test on phone)

## Configuration

### ✅ CORS (if needed)
If frontend and backend are on different domains:
- [ ] Update `allow_origins` in `app/api.py`
- [ ] Add your frontend URL to allowed origins
- [ ] Redeploy backend

### ✅ Environment Variables (optional)
For added security, consider:
- [ ] Set `OPENAI_API_KEY` in backend env
- [ ] Set `COHERE_API_KEY` in backend env
- [ ] Update API to use env vars as fallback
- [ ] Remove API key inputs from frontend

## Documentation

### ✅ Update README
- [ ] Add deployed URLs to README
- [ ] Update deployment section
- [ ] Add screenshot of deployed app

### ✅ Share Access
- [ ] Share frontend URL with users
- [ ] Provide instructions for API keys
- [ ] Document any known limitations

## Monitoring (Optional but Recommended)

### ✅ Set Up Monitoring
- [ ] Enable Vercel Analytics
- [ ] Monitor error logs
- [ ] Set up uptime monitoring
- [ ] Track API usage/costs

### ✅ Error Handling
- [ ] Test with invalid API key
- [ ] Test with backend down
- [ ] Test with slow network
- [ ] Verify error messages are helpful

## Troubleshooting Common Issues

### Backend won't deploy
- Check `requirements.txt` has all dependencies
- Verify Python version (3.9+)
- Check logs in Vercel/Railway dashboard

### Frontend won't deploy
- Run `npm run build` locally first
- Check for TypeScript errors
- Verify all dependencies in `package.json`

### Can't connect frontend to backend
- Check CORS settings in `app/api.py`
- Verify backend URL is correct
- Check browser console for errors
- Try with `http://` vs `https://`

### Data preparation fails
- Check PDF files exist in `data/newsletters/`
- Verify OpenAI API key is valid
- Check backend logs for errors
- May need to upload PDFs to backend server

## Success Criteria

Your deployment is successful when:
- ✅ Frontend loads at public URL
- ✅ Backend API responds at public URL
- ✅ Users can enter API keys and chat
- ✅ Agent returns relevant answers
- ✅ No errors in browser console
- ✅ Mobile responsive

## Next Steps

After successful deployment:
1. Share the app with beta users
2. Collect feedback
3. Monitor usage and costs
4. Plan feature enhancements
5. Consider adding authentication

## Support

Need help?
- Review [DEPLOYMENT.md](DEPLOYMENT.md)
- Check [QUICKSTART.md](QUICKSTART.md)
- Open GitHub issue
- Check Vercel/Railway documentation

---

**Deployment Date:** _____________

**Backend URL:** _____________

**Frontend URL:** _____________

**Deployed By:** _____________

