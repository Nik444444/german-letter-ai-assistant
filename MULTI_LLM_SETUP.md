# Multi-LLM Configuration Guide

## 🚀 Getting Started

This application now supports multiple LLM providers for maximum reliability and free usage optimization!

### 🔑 API Keys Setup

To use the multi-LLM system, you need to obtain API keys from various providers:

1. **Google Gemini** (Free tier: 15 requests/minute, 1000/day)
   - Visit: https://makersuite.google.com/app/apikey
   - Copy your API key and add to .env file

2. **OpenAI** (Free tier: $5 credit for new users)
   - Visit: https://platform.openai.com/api-keys
   - Create new API key and add to .env file

3. **Anthropic Claude** (Free tier: Limited usage)
   - Visit: https://console.anthropic.com/
   - Get your API key and add to .env file

4. **OpenRouter** (Free tier: Multiple free models)
   - Visit: https://openrouter.ai/keys
   - Get your API key and add to .env file

5. **Cohere** (Free tier: 100 requests/month)
   - Visit: https://dashboard.cohere.ai/api-keys
   - Get your API key and add to .env file

6. **Mistral AI** (Free tier: Limited usage)
   - Visit: https://console.mistral.ai/
   - Get your API key and add to .env file

7. **Hugging Face** (Free tier: Inference API)
   - Visit: https://huggingface.co/settings/tokens
   - Create new token and add to .env file

### 📝 Configuration

Edit `/app/backend/.env` file with your API keys:

```
GEMINI_API_KEY=your_actual_gemini_key_here
OPENAI_API_KEY=your_actual_openai_key_here
ANTHROPIC_API_KEY=your_actual_anthropic_key_here
OPENROUTER_API_KEY=your_actual_openrouter_key_here
COHERE_API_KEY=your_actual_cohere_key_here
MISTRAL_API_KEY=your_actual_mistral_key_here
HUGGINGFACE_API_KEY=your_actual_huggingface_key_here
```

### 🎯 How It Works

1. **Smart Fallback**: If one provider fails or reaches quota, automatically switches to next
2. **Priority System**: Providers are tried in order of priority (cheapest/most generous first)
3. **Quota Management**: Tracks usage and respects rate limits
4. **Error Handling**: Robust error handling with detailed logging

### 🛠 Testing

1. **Open Test Dashboard**: `/app/test_dashboard.html` in browser
2. **API Status**: `GET /api/llm-status`
3. **Test Providers**: `POST /api/test-llm`

### 📊 Monitoring

The system provides real-time monitoring of:
- Provider availability
- Usage statistics
- Error rates
- Response times
- Quota utilization

### 🔧 Customization

You can modify provider priorities and limits in `/app/backend/llm_manager.py`:

```python
# Example: Change provider priority
provider_configs = {
    "gemini": {..., "priority": 1},  # Highest priority
    "openai": {..., "priority": 2},  # Second priority
    ...
}
```

### 💡 Pro Tips

1. **Start with free tiers**: Get all free API keys first
2. **Monitor usage**: Check dashboard regularly
3. **Adjust priorities**: Put your most generous providers first
4. **Test regularly**: Use test endpoint to verify all providers work
5. **Scale gradually**: Add more providers as needed

### 🚨 Important Notes

- API keys are stored in environment variables
- Never commit real API keys to version control
- Test with small requests first
- Monitor your usage to avoid unexpected charges
- Some providers may require credit card even for free tier

## 🌟 Features

✅ **7 LLM Providers** supported out of the box
✅ **Smart Fallback** system
✅ **Quota Management** 
✅ **Real-time Monitoring**
✅ **Error Recovery**
✅ **Rate Limiting**
✅ **Usage Analytics**
✅ **Easy Configuration**

## 🎉 Ready to Use!

Your multi-LLM system is ready! Just add your API keys and start enjoying unlimited AI power with automatic fallbacks!