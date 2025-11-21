"""
Enhanced validation service with web search capabilities
"""

import re
import json
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import asyncio
import aiohttp

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Result of validation check"""
    is_valid: bool
    confidence: float
    issues: List[str]
    suggestions: List[str]
    web_search_results: Optional[Dict] = None

@dataclass
class CompensationBenchmark:
    """Industry compensation benchmarks"""
    min_ceo_comp: float
    max_ceo_comp: float
    min_cfo_comp: float
    max_cfo_comp: float
    min_other_exec_comp: float
    max_other_exec_comp: float

class EnhancedValidationService:
    """Enhanced validation service with web search and benchmarking"""
    
    def __init__(self, web_search_client=None, llm_client=None):
        self.web_search_client = web_search_client
        self.llm_client = llm_client
        
        # Industry compensation benchmarks (in millions)
        self.benchmarks = {
            'fortune_10': CompensationBenchmark(15.0, 50.0, 5.0, 20.0, 2.0, 15.0),
            'fortune_50': CompensationBenchmark(10.0, 40.0, 3.0, 15.0, 1.5, 12.0),
            'fortune_100': CompensationBenchmark(8.0, 35.0, 2.5, 12.0, 1.0, 10.0),
            'fortune_500': CompensationBenchmark(5.0, 25.0, 2.0, 10.0, 0.8, 8.0)
        }
        
        # Common executive title patterns
        self.exec_title_patterns = [
            r'chief executive officer|ceo',
            r'chief financial officer|cfo',
            r'chief operating officer|coo',
            r'chief technology officer|cto',
            r'president',
            r'executive vice president|evp',
            r'senior vice president|svp'
        ]
    
    async def validate_executive_data(self, company_name: str, company_rank: int, 
                                    executives: List[Dict]) -> ValidationResult:
        """Comprehensive validation of executive data"""
        issues = []
        suggestions = []
        web_results = {}
        
        try:
            # 1. Validate executive names with web search
            name_validation = await self._validate_executive_names(company_name, executives)
            issues.extend(name_validation.get('issues', []))
            suggestions.extend(name_validation.get('suggestions', []))
            web_results['name_validation'] = name_validation.get('search_results', {})
            
            # 2. Validate compensation ranges
            comp_validation = self._validate_compensation_ranges(company_rank, executives)
            issues.extend(comp_validation['issues'])
            suggestions.extend(comp_validation['suggestions'])
            
            # 3. Validate title consistency
            title_validation = self._validate_executive_titles(executives)
            issues.extend(title_validation['issues'])
            suggestions.extend(title_validation['suggestions'])
            
            # 4. Check for artificial patterns
            pattern_validation = self._detect_artificial_patterns(executives)
            issues.extend(pattern_validation['issues'])
            suggestions.extend(pattern_validation['suggestions'])
            
            # Calculate overall confidence
            confidence = self._calculate_confidence(issues, len(executives))
            
            return ValidationResult(
                is_valid=len(issues) < 3,  # Valid if fewer than 3 major issues
                confidence=confidence,
                issues=issues,
                suggestions=suggestions,
                web_search_results=web_results
            )
            
        except Exception as e:
            logger.error(f"Validation error for {company_name}: {e}")
            return ValidationResult(
                is_valid=False,
                confidence=0.0,
                issues=[f"Validation failed: {str(e)}"],
                suggestions=["Manual review required"],
                web_search_results={}
            )
    
    async def _validate_executive_names(self, company_name: str, 
                                      executives: List[Dict]) -> Dict:
        """Validate executive names using web search"""
        if not self.web_search_client:
            return {'issues': [], 'suggestions': [], 'search_results': {}}
        
        issues = []
        suggestions = []
        search_results = {}
        
        try:
            # Search for company executives
            search_query = f"{company_name} executives leadership team CEO CFO 2024"
            search_response = await self.web_search_client(search_query, f"Finding executives for {company_name}")
            
            if search_response:
                search_results['leadership_search'] = search_response

                # Extract names from search results
                found_names = self._extract_names_from_search_text(search_response)
                
                # Validate each executive name
                for exec_data in executives:
                    exec_name = exec_data.get('name', '').strip()
                    
                    # Skip obviously invalid names
                    if self._is_invalid_name(exec_name):
                        issues.append(f"Invalid executive name: '{exec_name}'")
                        continue
                    
                    # Check if name appears in search results
                    name_match = self._find_name_match(exec_name, found_names)
                    if not name_match:
                        # Search specifically for this executive
                        exec_search_query = f"{exec_name} {company_name} executive"
                        exec_search = await self.web_search_client(exec_search_query, f"Validating {exec_name} at {company_name}")

                        if exec_search:
                            search_results[f'exec_search_{exec_name}'] = exec_search

                            # Check if executive is found at this company
                            if not self._validate_executive_at_company_text(exec_name, company_name, exec_search):
                                issues.append(f"Executive '{exec_name}' not found at {company_name}")
                                suggestions.append(f"Verify '{exec_name}' is current executive at {company_name}")
                
        except Exception as e:
            logger.error(f"Name validation error: {e}")
            issues.append(f"Name validation failed: {str(e)}")
        
        return {
            'issues': issues,
            'suggestions': suggestions,
            'search_results': search_results
        }
    
    def _validate_compensation_ranges(self, company_rank: int, 
                                    executives: List[Dict]) -> Dict:
        """Validate compensation against industry benchmarks"""
        issues = []
        suggestions = []
        
        # Determine benchmark category
        if company_rank <= 10:
            benchmark = self.benchmarks['fortune_10']
        elif company_rank <= 50:
            benchmark = self.benchmarks['fortune_50']
        elif company_rank <= 100:
            benchmark = self.benchmarks['fortune_100']
        else:
            benchmark = self.benchmarks['fortune_500']
        
        for exec_data in executives:
            total_comp = exec_data.get('total_compensation', 0) / 1_000_000  # Convert to millions
            title = exec_data.get('title', '').lower()
            name = exec_data.get('name', '')
            
            # Check CEO compensation
            if any(pattern in title for pattern in ['ceo', 'chief executive']):
                if total_comp < benchmark.min_ceo_comp:
                    issues.append(f"CEO {name} compensation (${total_comp:.1f}M) below expected range (${benchmark.min_ceo_comp}M-${benchmark.max_ceo_comp}M)")
                elif total_comp > benchmark.max_ceo_comp:
                    suggestions.append(f"CEO {name} compensation (${total_comp:.1f}M) above typical range - verify accuracy")
            
            # Check CFO compensation
            elif any(pattern in title for pattern in ['cfo', 'chief financial']):
                if total_comp < benchmark.min_cfo_comp:
                    issues.append(f"CFO {name} compensation (${total_comp:.1f}M) below expected range")
                elif total_comp > benchmark.max_cfo_comp:
                    suggestions.append(f"CFO {name} compensation (${total_comp:.1f}M) above typical range")
            
            # Check other executives
            else:
                if total_comp < benchmark.min_other_exec_comp:
                    issues.append(f"Executive {name} compensation (${total_comp:.1f}M) unusually low")
                elif total_comp > benchmark.max_other_exec_comp:
                    suggestions.append(f"Executive {name} compensation (${total_comp:.1f}M) unusually high")
        
        return {'issues': issues, 'suggestions': suggestions}

    def _validate_executive_titles(self, executives: List[Dict]) -> Dict:
        """Validate executive titles for consistency and realism"""
        issues = []
        suggestions = []

        titles = [exec_data.get('title', '').lower() for exec_data in executives]

        # Check for duplicate titles
        title_counts = {}
        for title in titles:
            if title:
                title_counts[title] = title_counts.get(title, 0) + 1

        for title, count in title_counts.items():
            if count > 1 and 'ceo' in title:
                issues.append(f"Multiple CEOs found: {count} executives with CEO title")
            elif count > 2:
                suggestions.append(f"Multiple executives with same title: '{title}' ({count} times)")

        # Check for valid executive titles
        for exec_data in executives:
            title = exec_data.get('title', '').lower()
            name = exec_data.get('name', '')

            if not title or title.strip() == '':
                issues.append(f"Missing title for executive: {name}")
            elif not any(re.search(pattern, title) for pattern in self.exec_title_patterns):
                if len(title) > 5:  # Avoid flagging very short titles
                    suggestions.append(f"Unusual executive title for {name}: '{title}'")

        return {'issues': issues, 'suggestions': suggestions}

    def _detect_artificial_patterns(self, executives: List[Dict]) -> Dict:
        """Detect artificial patterns in compensation data"""
        issues = []
        suggestions = []

        if len(executives) < 2:
            return {'issues': issues, 'suggestions': suggestions}

        # Check for identical compensation ratios
        ratios = []
        for exec_data in executives:
            total = exec_data.get('total_compensation', 0)
            if total > 0:
                salary_ratio = exec_data.get('salary', 0) / total
                bonus_ratio = exec_data.get('bonus', 0) / total
                stock_ratio = exec_data.get('stock_awards', 0) / total
                option_ratio = exec_data.get('option_awards', 0) / total
                ratios.append((salary_ratio, bonus_ratio, stock_ratio, option_ratio))

        # Check for identical ratios (artificial pattern)
        if len(ratios) > 1:
            first_ratio = ratios[0]
            identical_count = sum(1 for ratio in ratios if self._ratios_similar(first_ratio, ratio))

            if identical_count >= len(ratios) * 0.8:  # 80% or more have same ratios
                issues.append("Artificial compensation pattern detected: identical ratios across executives")
                suggestions.append("Verify compensation data - ratios appear artificially uniform")

        # Check for round numbers (potential artificial data)
        round_number_count = 0
        for exec_data in executives:
            total = exec_data.get('total_compensation', 0)
            if total > 0 and total % 1000000 == 0:  # Exact millions
                round_number_count += 1

        if round_number_count >= len(executives) * 0.6:  # 60% or more are round millions
            suggestions.append("Many executives have round million compensation - verify accuracy")

        return {'issues': issues, 'suggestions': suggestions}

    def _extract_names_from_search_text(self, search_text: str) -> List[str]:
        """Extract executive names from web search text response"""
        names = []

        # Look for common executive name patterns in the text
        text_lower = search_text.lower()

        # Simple name extraction patterns
        name_patterns = [
            r'ceo\s+([A-Z][a-z]+\s+[A-Z][a-z]+)',
            r'chief executive officer\s+([A-Z][a-z]+\s+[A-Z][a-z]+)',
            r'president\s+([A-Z][a-z]+\s+[A-Z][a-z]+)',
            r'([A-Z][a-z]+\s+[A-Z][a-z]+),?\s+ceo',
            r'([A-Z][a-z]+\s+[A-Z][a-z]+),?\s+chief executive',
            r'([A-Z][a-z]+\s+[A-Z][a-z]+)\s+serves as',
            r'([A-Z][a-z]+\s+[A-Z][a-z]+)\s+is the'
        ]

        for pattern in name_patterns:
            matches = re.findall(pattern, search_text)
            names.extend(matches)

        return list(set(names))  # Remove duplicates

    def _is_invalid_name(self, name: str) -> bool:
        """Check if name is obviously invalid"""
        invalid_patterns = [
            r'^(total|audit|director|the\s+\w+\s+company)$',
            r'^\$[\d,]+$',  # Dollar amounts
            r'^[\d\s,.-]+$',  # Only numbers and punctuation
            r'^(fees?|costs?|expenses?)$',
            r'^(n/a|tbd|pending)$'
        ]

        name_lower = name.lower().strip()
        return any(re.search(pattern, name_lower) for pattern in invalid_patterns)

    def _find_name_match(self, exec_name: str, found_names: List[str]) -> bool:
        """Find if executive name matches any found names"""
        exec_parts = exec_name.lower().split()

        for found_name in found_names:
            found_parts = found_name.lower().split()

            # Check for partial matches (first and last name)
            if len(exec_parts) >= 2 and len(found_parts) >= 2:
                if exec_parts[0] in found_parts and exec_parts[-1] in found_parts:
                    return True

        return False

    def _validate_executive_at_company_text(self, exec_name: str, company_name: str,
                                          search_text: str) -> bool:
        """Validate if executive works at the specified company"""
        text_lower = search_text.lower()
        exec_name_lower = exec_name.lower()
        company_name_lower = company_name.lower()

        # Check if both executive name and company appear together
        return exec_name_lower in text_lower and company_name_lower in text_lower

    def _ratios_similar(self, ratio1: Tuple[float, float, float, float],
                       ratio2: Tuple[float, float, float, float],
                       tolerance: float = 0.01) -> bool:
        """Check if two ratio tuples are similar within tolerance"""
        return all(abs(r1 - r2) < tolerance for r1, r2 in zip(ratio1, ratio2))

    def _calculate_confidence(self, issues: List[str], num_executives: int) -> float:
        """Calculate confidence score based on validation results"""
        if num_executives == 0:
            return 0.0

        # Base confidence
        confidence = 1.0

        # Reduce confidence for each issue
        for issue in issues:
            if 'artificial' in issue.lower() or 'invalid' in issue.lower():
                confidence -= 0.3  # Major issues
            elif 'not found' in issue.lower():
                confidence -= 0.2  # Name validation issues
            else:
                confidence -= 0.1  # Minor issues

        return max(0.0, min(1.0, confidence))
