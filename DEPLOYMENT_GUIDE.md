# Configuration and Deployment Guide

## Configuration Solutions Implemented

### Problem
The `.env` file is correctly excluded from git repositories for security, but this means Streamlit Cloud and other deployment platforms don't have access to environment variables.

### Solution: Multi-Source Configuration Management

We've implemented a robust configuration system that loads from multiple sources in order of priority:

1. **Streamlit Secrets** (for deployed apps)
2. **Environment Variables** (for containers/hosting)
3. **`.env` file** (for local development)

## Files Modified

### 1. Configuration Manager (`modules/config_manager.py`)
- Handles loading from all configuration sources
- Provides fallback mechanisms
- Includes status checking functionality

### 2. Updated Import Chain
- `app.py`: Uses configuration manager for main thread
- `processors.py`: Uses configuration manager for processing modules
- `simple_db.py`: Uses configuration manager for database connections

### 3. Streamlit Secrets (`/.streamlit/secrets.toml`)
- Local development secrets file
- **Should be added to `.gitignore`** (already done)
- Template for Streamlit Cloud secrets

## Deployment Instructions

### For Streamlit Cloud Deployment:

1. **Push your code** to GitHub (without the `.env` or `secrets.toml` files)

2. **Set up Streamlit Cloud Secrets:**
   - Go to your Streamlit Cloud app settings
   - Navigate to "Secrets" section
   - Add the following configuration:

```toml
[database]
SUPABASE_URL = "https://apeibqwsqntliuvvygvk.supabase.co"
SUPABASE_ANON_KEY = "your_supabase_anon_key_here"
SUPABASE_SERVICE_KEY = "your_supabase_service_key_here"
ENABLE_SUPABASE = "true"

[api_keys]
OPENAI_API_KEY = "your_openai_key_here"
MISTRAL_API_KEY = "your_mistral_key_here"
GOOGLE_API_KEY = "your_google_key_here"
```

3. **Redeploy** your Streamlit app

### For Other Hosting Platforms:

Set these environment variables in your hosting platform:

```bash
SUPABASE_URL=https://apeibqwsqntliuvvygvk.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key_here
SUPABASE_SERVICE_KEY=your_supabase_service_key_here
ENABLE_SUPABASE=true
OPENAI_API_KEY=your_openai_key_here
MISTRAL_API_KEY=your_mistral_key_here
GOOGLE_API_KEY=your_google_key_here
```

## Testing Configuration

### Local Testing:
```bash
python test_config.py
```

### In Streamlit App:
- Use the "🔧 Configuration Status" expandable section in the app
- Check that all variables show ✅ with correct sources

## Security Best Practices

1. **Never commit** `.env` or `secrets.toml` files to git
2. **Rotate API keys** regularly
3. **Use different keys** for development vs production
4. **Monitor API usage** for unusual activity

## Troubleshooting

### Configuration Not Loading:
1. Check the "Configuration Status" section in the app
2. Run `python test_config.py` locally
3. Verify file paths and permissions

### Database Connection Issues:
1. Ensure `ENABLE_SUPABASE=true`
2. Verify Supabase URL and keys are correct
3. Check Supabase service status

### API Key Issues:
1. Verify keys are properly formatted (no extra spaces)
2. Check API key permissions and quotas
3. Test keys individually in separate scripts

## Configuration Priority Order

1. **Streamlit Secrets** → Deployed apps
2. **Environment Variables** → Container deployments
3. **`.env` file** → Local development

This ensures your app works across all deployment scenarios while maintaining security best practices.
