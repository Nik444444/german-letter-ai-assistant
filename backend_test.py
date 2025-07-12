#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for German Letter AI Assistant
Tests all backend endpoints with various scenarios
"""

import requests
import json
import sys
import os
from datetime import datetime

# Get backend URL from frontend .env file
def get_backend_url():
    try:
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    return line.split('=', 1)[1].strip()
    except Exception as e:
        print(f"Error reading frontend .env: {e}")
    return "https://german-letter-ai-assistant.onrender.com"

BASE_URL = get_backend_url()
API_URL = f"{BASE_URL}/api"

print(f"Testing backend API at: {API_URL}")
print("=" * 60)

def test_health_endpoint():
    """Test /api/health endpoint"""
    print("\n1. Testing Health Endpoint (/api/health)")
    print("-" * 40)
    
    try:
        response = requests.get(f"{API_URL}/health", timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            data = response.json()
            if "status" in data and data["status"] == "healthy":
                print("✅ Health check PASSED")
                return True
            else:
                print("❌ Health check FAILED - Invalid response format")
                return False
        else:
            print(f"❌ Health check FAILED - Status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Health check FAILED - Error: {str(e)}")
        return False

def test_llm_status_endpoint():
    """Test /api/llm-status endpoint"""
    print("\n2. Testing LLM Status Endpoint (/api/llm-status)")
    print("-" * 40)
    
    try:
        response = requests.get(f"{API_URL}/llm-status", timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            # Check if response has expected structure
            if "status" in data and "providers" in data:
                print(f"Total providers: {data.get('total_providers', 'N/A')}")
                print(f"Active providers: {data.get('active_providers', 'N/A')}")
                
                # Check for active providers
                providers = data.get("providers", {})
                active_providers = []
                for name, info in providers.items():
                    if info.get("status") == "active":
                        active_providers.append(name)
                
                if active_providers:
                    print(f"✅ LLM Status check PASSED - Active providers: {', '.join(active_providers)}")
                    return True, active_providers
                else:
                    print("⚠️ LLM Status check WARNING - No active providers found")
                    return True, []
            else:
                print("❌ LLM Status check FAILED - Invalid response format")
                return False, []
        else:
            print(f"❌ LLM Status check FAILED - Status code: {response.status_code}")
            return False, []
            
    except Exception as e:
        print(f"❌ LLM Status check FAILED - Error: {str(e)}")
        return False, []

def test_analyze_text_russian():
    """Test /api/analyze-text with German text in Russian language"""
    print("\n3. Testing Text Analysis - Russian Language")
    print("-" * 40)
    
    german_text = """Sehr geehrte Damen und Herren, hiermit teilen wir Ihnen mit, dass Ihr Antrag vom 15. Januar 2024 genehmigt wurde. Sie haben 30 Tage Zeit, um die erforderlichen Dokumente einzureichen. Mit freundlichen Grüßen, Jobcenter Hamburg"""
    
    payload = {
        "text": german_text,
        "language": "ru"
    }
    
    try:
        response = requests.post(
            f"{API_URL}/analyze-text", 
            json=payload, 
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"LLM Provider Used: {data.get('llm_provider', 'N/A')}")
            print(f"Summary: {data.get('summary', 'N/A')}")
            
            # Check required fields
            required_fields = ['analysis', 'summary', 'actions_needed', 'deadlines']
            missing_fields = [field for field in required_fields if field not in data]
            
            if not missing_fields:
                analysis = data.get('analysis', {})
                if isinstance(analysis, dict) and 'error' not in analysis:
                    print("✅ Russian text analysis PASSED")
                    print(f"Actions needed: {len(data.get('actions_needed', []))} items")
                    print(f"Deadlines: {len(data.get('deadlines', []))} items")
                    return True
                else:
                    print(f"❌ Russian text analysis FAILED - Analysis contains error: {analysis}")
                    return False
            else:
                print(f"❌ Russian text analysis FAILED - Missing fields: {missing_fields}")
                return False
        else:
            print(f"❌ Russian text analysis FAILED - Status code: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error details: {error_data}")
            except:
                print(f"Error response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Russian text analysis FAILED - Error: {str(e)}")
        return False

def test_analyze_text_english():
    """Test /api/analyze-text with German text in English language"""
    print("\n4. Testing Text Analysis - English Language")
    print("-" * 40)
    
    german_text = """Sehr geehrte Damen und Herren, hiermit teilen wir Ihnen mit, dass Ihr Antrag vom 15. Januar 2024 genehmigt wurde. Sie haben 30 Tage Zeit, um die erforderlichen Dokumente einzureichen. Mit freundlichen Grüßen, Jobcenter Hamburg"""
    
    payload = {
        "text": german_text,
        "language": "en"
    }
    
    try:
        response = requests.post(
            f"{API_URL}/analyze-text", 
            json=payload, 
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"LLM Provider Used: {data.get('llm_provider', 'N/A')}")
            print(f"Summary: {data.get('summary', 'N/A')}")
            
            # Check required fields
            required_fields = ['analysis', 'summary', 'actions_needed', 'deadlines']
            missing_fields = [field for field in required_fields if field not in data]
            
            if not missing_fields:
                analysis = data.get('analysis', {})
                if isinstance(analysis, dict) and 'error' not in analysis:
                    print("✅ English text analysis PASSED")
                    print(f"Actions needed: {len(data.get('actions_needed', []))} items")
                    print(f"Deadlines: {len(data.get('deadlines', []))} items")
                    return True
                else:
                    print(f"❌ English text analysis FAILED - Analysis contains error: {analysis}")
                    return False
            else:
                print(f"❌ English text analysis FAILED - Missing fields: {missing_fields}")
                return False
        else:
            print(f"❌ English text analysis FAILED - Status code: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error details: {error_data}")
            except:
                print(f"Error response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ English text analysis FAILED - Error: {str(e)}")
        return False

def test_short_text():
    """Test with short German text"""
    print("\n5. Testing Short Text Analysis")
    print("-" * 40)
    
    short_text = "Sehr geehrte Damen und Herren, Ihr Antrag wurde genehmigt."
    
    payload = {
        "text": short_text,
        "language": "en"
    }
    
    try:
        response = requests.post(
            f"{API_URL}/analyze-text", 
            json=payload, 
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"LLM Provider Used: {data.get('llm_provider', 'N/A')}")
            print("✅ Short text analysis PASSED")
            return True
        else:
            print(f"❌ Short text analysis FAILED - Status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Short text analysis FAILED - Error: {str(e)}")
        return False

def test_long_text():
    """Test with long German text"""
    print("\n6. Testing Long Text Analysis")
    print("-" * 40)
    
    long_text = """Sehr geehrte Damen und Herren,

hiermit teilen wir Ihnen mit, dass Ihr Antrag auf Arbeitslosengeld II vom 15. Januar 2024 nach eingehender Prüfung genehmigt wurde. Die Bewilligung erfolgt für den Zeitraum vom 01. Februar 2024 bis zum 31. Januar 2025.

Ihre monatliche Leistung beträgt 502 Euro und wird jeweils zum Monatsende auf Ihr angegebenes Konto überwiesen. Zusätzlich erhalten Sie Kosten der Unterkunft in Höhe von 450 Euro monatlich.

Sie sind verpflichtet, folgende Dokumente bis zum 28. Februar 2024 einzureichen:
1. Mietvertrag oder Eigentumsnachweis
2. Nebenkostenabrechnungen der letzten 12 Monate
3. Kontoauszüge der letzten 3 Monate
4. Nachweis über Krankenversicherung

Sollten Sie diese Unterlagen nicht fristgerecht einreichen, kann die Bewilligung widerrufen werden. Bei Änderungen Ihrer persönlichen oder wirtschaftlichen Verhältnisse sind Sie verpflichtet, diese unverzüglich mitzuteilen.

Für Rückfragen stehen wir Ihnen gerne zur Verfügung.

Mit freundlichen Grüßen
Jobcenter Hamburg
Sachbearbeiter: Herr Müller
Telefon: 040-123456789"""
    
    payload = {
        "text": long_text,
        "language": "en"
    }
    
    try:
        response = requests.post(
            f"{API_URL}/analyze-text", 
            json=payload, 
            headers={"Content-Type": "application/json"},
            timeout=90
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"LLM Provider Used: {data.get('llm_provider', 'N/A')}")
            print("✅ Long text analysis PASSED")
            return True
        else:
            print(f"❌ Long text analysis FAILED - Status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Long text analysis FAILED - Error: {str(e)}")
        return False

def test_empty_text():
    """Test error handling with empty text"""
    print("\n7. Testing Empty Text Error Handling")
    print("-" * 40)
    
    payload = {
        "text": "",
        "language": "en"
    }
    
    try:
        response = requests.post(
            f"{API_URL}/analyze-text", 
            json=payload, 
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        # Empty text should either be handled gracefully or return an error
        if response.status_code in [200, 400, 422]:
            print("✅ Empty text handling PASSED (handled appropriately)")
            return True
        else:
            print(f"❌ Empty text handling FAILED - Unexpected status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Empty text handling FAILED - Error: {str(e)}")
        return False

def main():
    """Run all backend tests"""
    print("German Letter AI Assistant - Backend API Testing")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    results = {}
    
    # Test 1: Health check
    results['health'] = test_health_endpoint()
    
    # Test 2: LLM status
    llm_status_result, active_providers = test_llm_status_endpoint()
    results['llm_status'] = llm_status_result
    
    # Test 3: Russian text analysis
    results['russian_analysis'] = test_analyze_text_russian()
    
    # Test 4: English text analysis
    results['english_analysis'] = test_analyze_text_english()
    
    # Test 5: Short text
    results['short_text'] = test_short_text()
    
    # Test 6: Long text
    results['long_text'] = test_long_text()
    
    # Test 7: Empty text
    results['empty_text'] = test_empty_text()
    
    # Summary
    print("\n" + "=" * 60)
    print("BACKEND API TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if active_providers:
        print(f"Active LLM Providers: {', '.join(active_providers)}")
    
    # Return success if critical tests pass
    critical_tests = ['health', 'llm_status', 'russian_analysis', 'english_analysis']
    critical_passed = all(results.get(test, False) for test in critical_tests)
    
    if critical_passed:
        print("\n🎉 All critical backend tests PASSED!")
        return True
    else:
        print("\n⚠️ Some critical backend tests FAILED!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)