# free_tools.py
# Free external APIs for real-time information

import logging
from typing import Dict, Optional
import requests

logger = logging.getLogger(__name__)

# Wikipedia API
try:
    import wikipedia
    WIKIPEDIA_AVAILABLE = True
except ImportError:
    WIKIPEDIA_AVAILABLE = False
    logger.warning("Wikipedia module not available. Install with: pip install wikipedia")


class WikipediaTool:
    """Search Wikipedia for general knowledge"""
    
    @staticmethod
    def search(query: str, sentences: int = 3) -> Dict:
        """
        Search Wikipedia and return summary
        
        Args:
            query: Search query
            sentences: Number of sentences in summary
        
        Returns:
            {
                'summary': str,
                'url': str,
                'title': str,
                'success': bool
            }
        """
        if not WIKIPEDIA_AVAILABLE:
            return {
                'summary': "Wikipedia integration not available.",
                'success': False,
                'error': 'Module not installed'
            }
        
        try:
            # Search and get best match
            search_results = wikipedia.search(query, results=1)
            
            if not search_results:
                return {
                    'summary': f"No Wikipedia results found for: {query}",
                    'success': False
                }
            
            # Get page summary
            page = wikipedia.page(search_results[0], auto_suggest=False)
            summary = wikipedia.summary(search_results[0], sentences=sentences)
            
            return {
                'summary': summary,
                'url': page.url,
                'title': page.title,
                'success': True
            }
        
        except wikipedia.exceptions.DisambiguationError as e:
            # Multiple matches, use first option
            try:
                page = wikipedia.page(e.options[0], auto_suggest=False)
                summary = wikipedia.summary(e.options[0], sentences=sentences)
                return {
                    'summary': summary,
                    'url': page.url,
                    'title': page.title,
                    'success': True,
                    'note': f'Disambiguated to: {e.options[0]}'
                }
            except Exception as inner_e:
                logger.exception(f"Disambiguation fallback failed: {inner_e}")
                return {
                    'summary': f"Multiple meanings found. Try: {', '.join(e.options[:3])}",
                    'success': False
                }
        
        except Exception as e:
            logger.exception(f"Wikipedia search failed: {e}")
            return {
                'summary': f"Wikipedia search error: {str(e)}",
                'success': False,
                'error': str(e)
            }


class WeatherTool:
    """Get weather information using AccuWeather API"""
    
    # Get free API key from: https://developer.accuweather.com/
    # Free tier: 50 calls/day
    
    @staticmethod
    def get_weather(location: str, api_key: str = None) -> Dict:
        """
        Get current weather for a location using AccuWeather
        
        Args:
            location: City name or "City, Country"
            api_key: AccuWeather API key (optional, read from env)
        
        Returns:
            {
                'temperature': float,
                'description': str,
                'humidity': int,
                'wind_speed': float,
                'location': str,
                'success': bool
            }
        """
        import os
        
        # Get API key from parameter or environment
        api_key = api_key or os.environ.get('ACCUWEATHER_API_KEY')
        
        if not api_key:
            return {
                'description': "Weather API key not configured. Set ACCUWEATHER_API_KEY environment variable.",
                'success': False,
                'error': 'API key missing'
            }
        
        try:
            # Step 1: Get location key from city name
            location_url = "http://dataservice.accuweather.com/locations/v1/cities/search"
            location_params = {
                'apikey': api_key,
                'q': location
            }
            
            location_response = requests.get(location_url, params=location_params, timeout=5)
            location_response.raise_for_status()
            
            location_data = location_response.json()
            
            if not location_data or len(location_data) == 0:
                return {
                    'description': f"Location '{location}' not found. Try including country name.",
                    'success': False,
                    'error': 'Location not found'
                }
            
            # Get the first match
            location_key = location_data[0]['Key']
            location_name = location_data[0]['LocalizedName']
            country = location_data[0]['Country']['LocalizedName']
            
            # Step 2: Get current conditions using location key
            weather_url = f"http://dataservice.accuweather.com/currentconditions/v1/{location_key}"
            weather_params = {
                'apikey': api_key,
                'details': 'true'
            }
            
            weather_response = requests.get(weather_url, params=weather_params, timeout=5)
            weather_response.raise_for_status()
            
            weather_data = weather_response.json()
            
            if not weather_data or len(weather_data) == 0:
                return {
                    'description': f"Weather data not available for '{location}'",
                    'success': False,
                    'error': 'No weather data'
                }
            
            current = weather_data[0]
            
            return {
                'temperature': float(current['Temperature']['Metric']['Value']),
                'feels_like': float(current.get('RealFeelTemperature', {}).get('Metric', {}).get('Value', current['Temperature']['Metric']['Value'])),
                'description': current['WeatherText'].lower(),
                'humidity': int(current.get('RelativeHumidity', 0)),
                'wind_speed': float(current.get('Wind', {}).get('Speed', {}).get('Metric', {}).get('Value', 0)) / 3.6,  # Convert km/h to m/s
                'location': f"{location_name}, {country}",
                'success': True
            }
        
        except requests.exceptions.Timeout:
            return {
                'description': "Weather service timeout. Please try again.",
                'success': False,
                'error': 'Timeout'
            }
        
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                return {
                    'description': "Invalid AccuWeather API key. Please check your ACCUWEATHER_API_KEY.",
                    'success': False,
                    'error': 'Invalid API key'
                }
            elif e.response.status_code == 404:
                return {
                    'description': f"Location '{location}' not found. Try including country name.",
                    'success': False,
                    'error': 'Location not found'
                }
            else:
                return {
                    'description': f"Weather service error: {e.response.status_code}",
                    'success': False,
                    'error': str(e)
                }
        
        except KeyError as e:
            logger.exception(f"AccuWeather data parsing error: {e}")
            return {
                'description': f"Could not parse weather data for '{location}'",
                'success': False,
                'error': 'Parse error'
            }
        
        except Exception as e:
            logger.exception(f"Weather API failed: {e}")
            return {
                'description': f"Weather service unavailable: {str(e)}",
                'success': False,
                'error': str(e)
            }


class CalculatorTool:
    """Safe mathematical calculations"""
    
    @staticmethod
    def calculate(expression: str) -> Dict:
        """
        Safely evaluate mathematical expressions
        
        Args:
            expression: Math expression like "2 + 2" or "sqrt(16)"
        
        Returns:
            {
                'result': float,
                'expression': str,
                'success': bool
            }
        """
        import ast
        import operator
        import math
        
        # Allowed operations
        operators = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Pow: operator.pow,
            ast.USub: operator.neg,
        }
        
        # Allowed functions
        functions = {
            'sqrt': math.sqrt,
            'sin': math.sin,
            'cos': math.cos,
            'tan': math.tan,
            'log': math.log,
            'abs': abs,
            'round': round,
        }
        
        def eval_expr(node):
            if isinstance(node, ast.Num):
                return node.n
            elif isinstance(node, ast.BinOp):
                return operators[type(node.op)](eval_expr(node.left), eval_expr(node.right))
            elif isinstance(node, ast.UnaryOp):
                return operators[type(node.op)](eval_expr(node.operand))
            elif isinstance(node, ast.Call):
                func_name = node.func.id
                if func_name in functions:
                    args = [eval_expr(arg) for arg in node.args]
                    return functions[func_name](*args)
                else:
                    raise ValueError(f"Function '{func_name}' not allowed")
            else:
                raise TypeError(f"Unsupported operation: {node}")
        
        try:
            # Parse expression
            node = ast.parse(expression, mode='eval').body
            result = eval_expr(node)
            
            return {
                'result': result,
                'expression': expression,
                'success': True
            }
        except Exception as e:
            logger.exception(f"Calculation failed: {e}")
            return {
                'result': None,
                'expression': expression,
                'success': False,
                'error': str(e)
            }


# Convenience functions
def search_wikipedia(query: str) -> Dict:
    """Search Wikipedia"""
    return WikipediaTool.search(query)


def get_weather(location: str, api_key: str = None) -> Dict:
    """Get weather for location"""
    return WeatherTool.get_weather(location, api_key)


def calculate(expression: str) -> Dict:
    """Calculate mathematical expression"""
    return CalculatorTool.calculate(expression)
