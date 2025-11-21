"""
Comprehensive QA Controller for executive compensation data
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import asyncio

logger = logging.getLogger(__name__)

@dataclass
class QAResult:
    """Result of QA validation"""
    is_valid: bool
    confidence_score: float
    issues: List[str]
    corrections: Dict[str, Any]
    cleaned_data: Optional[Dict] = None

class ComprehensiveQAController:
    """Comprehensive QA controller for executive compensation data"""
    
    def __init__(self, llm_service=None, web_search_enabled=True):
        self.llm_service = llm_service
        self.web_search_enabled = web_search_enabled
        
        # Known invalid name patterns
        self.invalid_name_patterns = [
            r'^(total|audit|director|the\s+\w+\s+company)$',
            r'^\$[\d,]+$',  # Dollar amounts
            r'^[\d\s,.-]+$',  # Only numbers and punctuation
            r'^(fees?|costs?|expenses?)$',
            r'^(n/a|tbd|pending|none)$',
            r'^(chief|executive|officer|president)$',  # Just titles
            r'^\s*$'  # Empty or whitespace only
        ]
        
        # Known artificial ratio patterns
        self.artificial_ratios = [
            (0.30, 0.20, 0.40, 0.10),  # 30/20/40/10
            (0.25, 0.25, 0.25, 0.25),  # Equal quarters
            (0.33, 0.33, 0.34, 0.00),  # Equal thirds
        ]
        
        # Executive title patterns for validation
        self.valid_title_patterns = [
            r'chief executive officer|ceo',
            r'chief financial officer|cfo',
            r'chief operating officer|coo',
            r'chief technology officer|cto',
            r'president',
            r'chairman',
            r'vice president|vp',
            r'executive vice president|evp',
            r'senior vice president|svp'
        ]
        
        # Compensation reasonableness ranges (in millions)
        self.compensation_ranges = {
            'fortune_10': {'min': 15, 'max': 100, 'typical_max': 50},
            'fortune_50': {'min': 8, 'max': 80, 'typical_max': 40},
            'fortune_100': {'min': 5, 'max': 60, 'typical_max': 30},
            'fortune_500': {'min': 2, 'max': 40, 'typical_max': 20}
        }
    
    async def qa_executive_data(self, company_data: Dict) -> QAResult:
        """Comprehensive QA of executive data for a company"""
        company_name = company_data.get('name', '')
        company_rank = company_data.get('rank', 999)
        executives = company_data.get('executives', [])
        
        if not executives:
            return QAResult(
                is_valid=False,
                confidence_score=0.0,
                issues=['No executive data found'],
                corrections={}
            )
        
        issues = []
        corrections = {}
        cleaned_executives = []
        
        # 1. Validate and clean executive names
        name_results = await self._validate_executive_names(company_name, executives)
        issues.extend(name_results['issues'])
        corrections.update(name_results['corrections'])
        
        # 2. Validate compensation patterns
        comp_results = self._validate_compensation_patterns(executives, company_rank)
        issues.extend(comp_results['issues'])
        corrections.update(comp_results['corrections'])
        
        # 3. Validate titles
        title_results = self._validate_titles(executives)
        issues.extend(title_results['issues'])
        corrections.update(title_results['corrections'])
        
        # 4. Clean and format data
        for i, exec_data in enumerate(executives):
            cleaned_exec = await self._clean_executive_data(exec_data, company_name, corrections)
            if cleaned_exec:
                cleaned_executives.append(cleaned_exec)
        
        # 5. Calculate confidence score
        confidence_score = self._calculate_confidence_score(issues, len(executives))
        
        # 6. Final validation
        is_valid = confidence_score >= 0.6 and len(cleaned_executives) > 0
        
        return QAResult(
            is_valid=is_valid,
            confidence_score=confidence_score,
            issues=issues,
            corrections=corrections,
            cleaned_data={
                **company_data,
                'executives': cleaned_executives,
                'qa_metadata': {
                    'original_executive_count': len(executives),
                    'cleaned_executive_count': len(cleaned_executives),
                    'confidence_score': confidence_score,
                    'major_issues': len([i for i in issues if 'invalid' in i.lower() or 'artificial' in i.lower()])
                }
            }
        )
    
    async def _validate_executive_names(self, company_name: str, executives: List[Dict]) -> Dict:
        """Validate executive names and suggest corrections"""
        issues = []
        corrections = {}
        
        for i, exec_data in enumerate(executives):
            name = exec_data.get('name', '').strip()
            
            # Check for invalid patterns
            if self._is_invalid_name(name):
                issues.append(f"Invalid executive name: '{name}'")
                corrections[f'executive_{i}_name'] = 'REMOVE'
                continue
            
            # Check for concatenated title in name
            cleaned_name = self._separate_name_and_title(name)
            if cleaned_name != name:
                corrections[f'executive_{i}_name'] = cleaned_name
                corrections[f'executive_{i}_title_from_name'] = name.replace(cleaned_name, '').strip()
            
            # Web search validation if enabled
            if self.web_search_enabled and self.llm_service:
                try:
                    is_valid_exec = await self._web_validate_executive(company_name, cleaned_name)
                    if not is_valid_exec:
                        issues.append(f"Executive '{cleaned_name}' not found at {company_name}")
                        corrections[f'executive_{i}_confidence'] = 'LOW'
                except Exception as e:
                    logger.warning(f"Web validation failed for {cleaned_name}: {e}")
        
        return {'issues': issues, 'corrections': corrections}
    
    def _validate_compensation_patterns(self, executives: List[Dict], company_rank: int) -> Dict:
        """Validate compensation patterns for artificial data"""
        issues = []
        corrections = {}
        
        # Get appropriate compensation range
        if company_rank <= 10:
            comp_range = self.compensation_ranges['fortune_10']
        elif company_rank <= 50:
            comp_range = self.compensation_ranges['fortune_50']
        elif company_rank <= 100:
            comp_range = self.compensation_ranges['fortune_100']
        else:
            comp_range = self.compensation_ranges['fortune_500']
        
        artificial_pattern_count = 0
        
        for i, exec_data in enumerate(executives):
            total_comp = exec_data.get('total_compensation', 0)
            salary = exec_data.get('salary', 0)
            bonus = exec_data.get('bonus', 0)
            stock = exec_data.get('stock_awards', 0)
            options = exec_data.get('option_awards', 0)
            
            # Check for artificial ratios
            if total_comp > 0:
                ratios = (
                    salary / total_comp,
                    bonus / total_comp,
                    stock / total_comp,
                    options / total_comp
                )
                
                for artificial_ratio in self.artificial_ratios:
                    if self._ratios_match(ratios, artificial_ratio, tolerance=0.001):
                        artificial_pattern_count += 1
                        issues.append(f"Executive {i+1}: Artificial compensation ratio detected")
                        corrections[f'executive_{i}_artificial_pattern'] = True
                        break
            
            # Check compensation reasonableness
            total_comp_millions = total_comp / 1_000_000
            if total_comp_millions < comp_range['min']:
                issues.append(f"Executive {i+1}: Compensation unusually low (${total_comp_millions:.1f}M)")
            elif total_comp_millions > comp_range['typical_max']:
                issues.append(f"Executive {i+1}: Compensation unusually high (${total_comp_millions:.1f}M)")
        
        # Flag if too many artificial patterns
        if artificial_pattern_count >= len(executives) * 0.8:
            issues.append("Majority of executives show artificial compensation patterns")
            corrections['data_quality'] = 'ARTIFICIAL'
        
        return {'issues': issues, 'corrections': corrections}

    def _validate_titles(self, executives: List[Dict]) -> Dict:
        """Validate executive titles"""
        issues = []
        corrections = {}

        titles = []
        for i, exec_data in enumerate(executives):
            title = exec_data.get('title', '').strip().lower()

            if not title:
                issues.append(f"Executive {i+1}: Missing title")
                corrections[f'executive_{i}_title'] = 'MISSING'
                continue

            # Check for valid executive title patterns
            if not any(re.search(pattern, title) for pattern in self.valid_title_patterns):
                issues.append(f"Executive {i+1}: Unusual title '{title}'")
                corrections[f'executive_{i}_title_unusual'] = True

            titles.append(title)

        # Check for duplicate CEO titles
        ceo_count = sum(1 for title in titles if 'ceo' in title or 'chief executive' in title)
        if ceo_count > 1:
            issues.append(f"Multiple CEOs found ({ceo_count})")
            corrections['multiple_ceos'] = ceo_count

        return {'issues': issues, 'corrections': corrections}

    async def _clean_executive_data(self, exec_data: Dict, company_name: str, corrections: Dict) -> Optional[Dict]:
        """Clean and format executive data"""
        name = exec_data.get('name', '').strip()

        # Skip if marked for removal
        exec_index = None
        for key, value in corrections.items():
            if 'name' in key and value == 'REMOVE' and name in str(exec_data):
                return None

        # Clean name
        cleaned_name = self._separate_name_and_title(name)
        if self._is_invalid_name(cleaned_name):
            return None

        # Clean title
        title = exec_data.get('title', '').strip()
        if not title:
            # Try to extract title from name if it was concatenated
            for key, value in corrections.items():
                if 'title_from_name' in key and cleaned_name in name:
                    title = value
                    break

        # Clean compensation data
        total_comp = self._clean_numeric_value(exec_data.get('total_compensation', 0))
        salary = self._clean_numeric_value(exec_data.get('salary', 0))
        bonus = self._clean_numeric_value(exec_data.get('bonus', 0))
        stock = self._clean_numeric_value(exec_data.get('stock_awards', 0))
        options = self._clean_numeric_value(exec_data.get('option_awards', 0))

        # Validate compensation consistency
        calculated_total = salary + bonus + stock + options
        if total_comp > 0 and abs(calculated_total - total_comp) / total_comp > 0.1:
            # Recalculate total if components don't match
            total_comp = calculated_total

        return {
            'name': self._format_name(cleaned_name),
            'title': self._format_title(title),
            'total_compensation': total_comp,
            'salary': salary,
            'bonus': bonus,
            'stock_awards': stock,
            'option_awards': options,
            'other_compensation': max(0, total_comp - salary - bonus - stock - options)
        }

    def _is_invalid_name(self, name: str) -> bool:
        """Check if name matches invalid patterns"""
        if not name or len(name.strip()) < 2:
            return True

        name_lower = name.lower().strip()
        return any(re.search(pattern, name_lower) for pattern in self.invalid_name_patterns)

    def _separate_name_and_title(self, name_with_title: str) -> str:
        """Separate name from concatenated title"""
        # Common patterns where title is concatenated with name
        patterns = [
            r'^(.+?)\s+(Chief Executive Officer)$',
            r'^(.+?)\s+(Chief Financial Officer)$',
            r'^(.+?)\s+(Chief Operating Officer)$',
            r'^(.+?)\s+(President)$',
            r'^(.+?)\s+(Chairman)$'
        ]

        for pattern in patterns:
            match = re.search(pattern, name_with_title, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return name_with_title.strip()

    def _format_name(self, name: str) -> str:
        """Format executive name consistently"""
        # Remove extra whitespace and normalize
        name = ' '.join(name.split())

        # Capitalize properly
        parts = name.split()
        formatted_parts = []

        for part in parts:
            if '.' in part:  # Handle initials like "J."
                formatted_parts.append(part.upper())
            else:
                formatted_parts.append(part.capitalize())

        return ' '.join(formatted_parts)

    def _format_title(self, title: str) -> str:
        """Format executive title consistently"""
        if not title:
            return 'Executive'

        # Common title standardizations
        title_mappings = {
            'ceo': 'Chief Executive Officer',
            'cfo': 'Chief Financial Officer',
            'coo': 'Chief Operating Officer',
            'cto': 'Chief Technology Officer',
            'evp': 'Executive Vice President',
            'svp': 'Senior Vice President'
        }

        title_lower = title.lower().strip()

        # Check for exact matches
        if title_lower in title_mappings:
            return title_mappings[title_lower]

        # Check for partial matches
        for abbrev, full_title in title_mappings.items():
            if abbrev in title_lower:
                return full_title

        # Capitalize properly
        return ' '.join(word.capitalize() for word in title.split())

    def _clean_numeric_value(self, value: Any) -> float:
        """Clean and validate numeric compensation values"""
        if isinstance(value, (int, float)):
            return max(0.0, float(value))

        if isinstance(value, str):
            # Remove currency symbols and commas
            cleaned = re.sub(r'[^\d.-]', '', value)
            try:
                return max(0.0, float(cleaned))
            except ValueError:
                return 0.0

        return 0.0

    def _ratios_match(self, ratios1: Tuple[float, float, float, float],
                     ratios2: Tuple[float, float, float, float],
                     tolerance: float = 0.01) -> bool:
        """Check if two ratio tuples match within tolerance"""
        return all(abs(r1 - r2) < tolerance for r1, r2 in zip(ratios1, ratios2))

    async def _web_validate_executive(self, company_name: str, exec_name: str) -> bool:
        """Validate executive using web search"""
        try:
            if not self.llm_service:
                return True  # Skip validation if no LLM service

            query = f"{exec_name} {company_name} executive CEO CFO"
            response = await self.llm_service.web_search_request(query,
                f"Validating if {exec_name} is an executive at {company_name}")

            if response:
                # Simple validation - check if both names appear in response
                response_lower = response.lower()
                return (exec_name.lower() in response_lower and
                       company_name.lower() in response_lower)

            return True  # Default to valid if search fails

        except Exception as e:
            logger.warning(f"Web validation error: {e}")
            return True

    def _calculate_confidence_score(self, issues: List[str], executive_count: int) -> float:
        """Calculate confidence score based on issues found"""
        if executive_count == 0:
            return 0.0

        base_score = 1.0

        # Deduct points for different types of issues
        for issue in issues:
            issue_lower = issue.lower()

            if 'invalid' in issue_lower or 'artificial' in issue_lower:
                base_score -= 0.3  # Major issues
            elif 'not found' in issue_lower or 'unusual' in issue_lower:
                base_score -= 0.2  # Medium issues
            elif 'missing' in issue_lower or 'multiple' in issue_lower:
                base_score -= 0.1  # Minor issues
            else:
                base_score -= 0.05  # Other issues

        return max(0.0, min(1.0, base_score))
