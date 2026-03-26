# 🔐 Vercel Team Access Setup - Quick Guide

## Problem
Git author **Pawan95Kumar** needs access to the Vercel project to create deployments.

## Solution Overview
Add Pawan95Kumar as a **Project Member** or **Team Member** in Vercel with proper permissions.

---

## ✅ Step-by-Step Fix

### Option 1: Add as Project Member (Recommended for this project)

**Who should do this**: Current Vercel project owner

**Steps**:

1. **Go to Vercel Dashboard**
   - Visit: https://vercel.com/dashboard
   - Select your **claim360-email-app** project

2. **Open Project Settings**
   - Click **Settings** (top right menu)
   - Select **Members** from the left sidebar

3. **Add New Member**
   - Click **Add Member**
   - Enter Pawan95Kumar's **email address** or **Vercel username**
   - Ensure the following permissions are selected:
     - ✅ **View** (can view project and deployments)
     - ✅ **Create** (can trigger new deployments)
     - ✅ **Manage Environment Variables** (optional but recommended)

4. **Set Permission Role**
   - Select role: **Developer** or **Admin**
     - **Developer**: Can deploy, view logs, manage env vars
     - **Admin**: Full control including removing members
   - Recommendation: Use **Developer** unless Pawan95Kumar needs to manage team

5. **Save and Confirm**
   - Click **Add** to invite
   - An invitation email will be sent to Pawan95Kumar
   - They must accept the invitation to gain access

---

### Option 2: Add to Vercel Team (For multiple projects)

If Pawan95Kumar will work on multiple Vercel projects:

1. **Go to Team Settings**
   - Visit: https://vercel.com/dashboard/settings/team
   - Select your **team** (if using team billing)

2. **Manage Members**
   - Click **Members** tab
   - Click **Add Member**
   - Enter Pawan95Kumar's email

3. **Choose Team Role**
   - **Member**: Full project access
   - **Guest**: Limited access
   - Recommendation: Use **Member**

4. **Accept Invitation**
   - Pawan95Kumar will receive an email
   - Must click "Accept" to join the team

---

### Option 3: GitHub-based Deployment (Automatic)

If GitHub is connected and Pawan95Kumar is a GitHub collaborator:

1. **Ensure GitHub Integration**
   - Vercel Project Settings → Git Connector
   - Verify: "GitHub" is connected

2. **Add to GitHub Repository**
   - Go to: GitHub → claim360-email-app → Settings → Collaborators
   - Add Pawan95Kumar as **Collaborator** or **Maintainer**

3. **Auto-Deploy Setup** (Optional)
   - When Pawan95Kumar pushes to `main` branch, Vercel automatically deploys
   - No need to manually trigger deployment

**Permissions Required**:
- ✅ Pull/Push access to main branch
- ✅ Ability to create commits/PRs

---

## 🔑 Permission Levels Explained

| Permission | Can View | Can Deploy | Can Manage Env Vars | Can Remove Members |
|-----------|----------|-----------|-------------------|------------------|
| **Viewer** | ✅ | ❌ | ❌ | ❌ |
| **Developer** | ✅ | ✅ | ✅ | ❌ |
| **Admin** | ✅ | ✅ | ✅ | ✅ |

**Recommended for Pawan95Kumar**: **Developer** (can deploy without full admin control)

---

## ✅ Verification Checklist

After adding Pawan95Kumar, verify:

- [ ] Pawan95Kumar received invitation email
- [ ] Pawan95Kumar accepted the invitation
- [ ] Pawan95Kumar can log in to https://vercel.com/dashboard
- [ ] Pawan95Kumar can see the claim360-email-app project
- [ ] Pawan95Kumar can view deployments
- [ ] Pawan95Kumar can trigger a new deployment using `vercel --prod`
- [ ] Pawan95Kumar can view environment variables (if given permission)

---

## 🚀 For Pawan95Kumar: After Access is Granted

Once you have access, you can deploy using:

### Method 1: Vercel CLI

```bash
# Install Vercel CLI (one-time)
npm install -g vercel

# Deploy to production
vercel --prod

# Or deploy to staging
vercel

# View logs
vercel logs --prod
```

### Method 2: Vercel Dashboard

1. Go to: https://vercel.com/dashboard
2. Select: claim360-email-app project
3. Click: **Deploy** button (or redeploy from Deployments tab)

### Method 3: GitHub Auto-Deploy

Push to `main` branch:
```bash
git add -A
git commit -m "feat: your changes"
git push origin main
```
Vercel automatically deploys within 1-2 minutes.

---

## 🆘 Troubleshooting

### "You don't have permission to deploy"
**Solution**: Ensure your account has **Developer** or **Admin** role in project settings

### "Can't find project"
**Solution**: Vercel project owner must invite you → Check email for invitation → Accept

### "Environment variables not visible"
**Solution**: Your role doesn't allow viewing env vars → Ask project owner to upgrade settings

### "Deployment failed with permission error"
**Solution**: Check Vercel logs → Usually means database or API credentials issue, not access issue

---

## 📞 Next Steps

1. **Project Owner**: Add Pawan95Kumar using Steps 1-5 above
2. **Pawan95Kumar**: Accept the invitation email
3. **Verify**: Pawan95Kumar tests deployment with `vercel --prod`
4. **Document**: Save this guide for team reference

---

## 📊 Current Team Status

| Name | Email | Role | Access Level | Can Deploy |
|------|-------|------|--------------|-----------|
| (Project Owner) | — | Admin | Full | ✅ |
| Pawan95Kumar | — | Developer | Deploy Only | ✅ (after setup) |

---

## 🔒 Security Best Practices

- ✅ Use **Developer** role (not Admin) for individual developers
- ✅ Enable **GitHub integration** for automatic deployments when code is pushed
- ✅ Review **Environment Variables** access carefully (contains secrets)
- ✅ Remove members who no longer need access
- ✅ Use **GitHub branch protection** rules to prevent unreviewed code deployments

---

## 📚 References

- [Vercel Team Members Documentation](https://vercel.com/docs/accounts/team-management)
- [Vercel GitHub Integration](https://vercel.com/docs/git/vercel-for-github)
- [Vercel Deployments](https://vercel.com/docs/deployments)

---

**Last Updated**: March 26, 2026  
**Status**: ✅ Ready to implement
