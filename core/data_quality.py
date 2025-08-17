import pandas as pd
import re

# --- Enhanced Regex patterns ---
EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
DATE_RE = re.compile(
    r"^(?:\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]\d{4}|\d{4}\d{2}\d{2}|\d{2}\d{2}\d{4})$"
)  # supports YYYY-MM-DD, YYYY/MM/DD, DD-MM-YYYY, DD/MM/YYYY, YYYYMMDD, DDMMYYYY
PHONE_RE = re.compile(r"^[\+]?[1-9][\d]{0,15}$")
URL_RE = re.compile(r"^https?://(?:[-\w.])+(?:\:[0-9]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:\#(?:[\w.])*)?)?$")
POSTAL_CODE_RE = re.compile(r"^[A-Z0-9]{3,10}$")
CREDIT_CARD_RE = re.compile(r"^(?:\d{4}[-\s]?){3}\d{4}$")
IP_ADDRESS_RE = re.compile(r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$")


def comp(df: pd.DataFrame) -> dict:
    """Enhanced Completeness: % of non-null values per column with additional metrics"""
    if len(df) == 0:
        return {}
    
    completeness = {}
    for col in df.columns:
        non_null_count = df[col].notna().sum()
        null_count = df[col].isna().sum()
        empty_string_count = (df[col].astype(str).str.strip() == '').sum() if df[col].dtype == 'object' else 0
        
        completeness[col] = {
            "percentage": round((non_null_count / len(df)) * 100, 2),
            "non_null_count": int(non_null_count),
            "null_count": int(null_count),
            "empty_string_count": int(empty_string_count),
            "total_rows": len(df)
        }
    
    return completeness


def dup(df: pd.DataFrame) -> dict:
    """Enhanced Duplicates: comprehensive duplicate analysis"""
    if len(df) == 0:
        return {"total_rows": 0, "duplicate_rows": 0, "duplicate_percentage": 0, "unique_rows": 0}
    
    duplicate_rows = df.duplicated().sum()
    duplicate_percentage = round((duplicate_rows / len(df)) * 100, 2)
    unique_rows = len(df) - duplicate_rows
    
    # Find columns with high duplication rates
    column_duplicates = {}
    for col in df.columns:
        col_duplicates = df[col].duplicated().sum()
        column_duplicates[col] = {
            "duplicate_count": int(col_duplicates),
            "duplicate_percentage": round((col_duplicates / len(df)) * 100, 2),
            "unique_values": int(df[col].nunique())
        }
    
    return {
        "total_rows": len(df),
        "duplicate_rows": int(duplicate_rows),
        "duplicate_percentage": duplicate_percentage,
        "unique_rows": int(unique_rows),
        "column_duplicates": column_duplicates
    }


def cons(df: pd.DataFrame) -> dict:
    """Enhanced Consistency: comprehensive validation with data type detection"""
    if len(df) == 0:
        return {}
    
    consistency = {}
    
    for col in df.columns:
        col_data = df[col].dropna()
        if len(col_data) == 0:
            consistency[col] = {
                "invalid_count": 0,
                "invalid_percentage": 0,
                "data_type": "empty",
                "format_issues": [],
                "suggestions": []
            }
            continue
            
        invalid_count = 0
        format_issues = []
        suggestions = []
        detected_type = "unknown"
        
        if col_data.dtype == "object":
            str_data = col_data.astype(str).str.strip()
            col_lower = col.lower()
            
            # Email validation
            if any(keyword in col_lower for keyword in ["email", "mail", "@"]):
                detected_type = "email"
                invalid_mask = ~str_data.str.match(EMAIL_RE, na=False)
                invalid_count = invalid_mask.sum()
                if invalid_count > 0:
                    format_issues.append("Invalid email formats detected")
                    suggestions.append("Ensure emails follow format: user@domain.com")
            
            # Phone validation
            elif any(keyword in col_lower for keyword in ["phone", "tel", "mobile", "cell"]):
                detected_type = "phone"
                # Clean phone numbers for validation
                cleaned_phones = str_data.str.replace(r'[\s\-\(\)]', '', regex=True)
                invalid_mask = ~cleaned_phones.str.match(PHONE_RE, na=False)
                invalid_count = invalid_mask.sum()
                if invalid_count > 0:
                    format_issues.append("Invalid phone number formats")
                    suggestions.append("Use international format: +1234567890")
            
            # Date validation
            elif any(keyword in col_lower for keyword in ["date", "time", "created", "updated", "birth"]):
                detected_type = "date"
                invalid_mask = ~str_data.str.match(DATE_RE, na=False)
                invalid_count = invalid_mask.sum()
                if invalid_count > 0:
                    format_issues.append("Inconsistent date formats")
                    suggestions.append("Standardize date format (YYYY-MM-DD recommended)")
            
            # URL validation
            elif any(keyword in col_lower for keyword in ["url", "link", "website", "http"]):
                detected_type = "url"
                invalid_mask = ~str_data.str.match(URL_RE, na=False)
                invalid_count = invalid_mask.sum()
                if invalid_count > 0:
                    format_issues.append("Invalid URL formats")
                    suggestions.append("URLs should start with http:// or https://")
            
            # Postal code validation
            elif any(keyword in col_lower for keyword in ["postal", "zip", "postcode"]):
                detected_type = "postal_code"
                invalid_mask = ~str_data.str.upper().str.match(POSTAL_CODE_RE, na=False)
                invalid_count = invalid_mask.sum()
                if invalid_count > 0:
                    format_issues.append("Invalid postal code formats")
                    suggestions.append("Use standard postal code format for your region")
            
            # General text analysis
            else:
                detected_type = "text"
                # Check for excessive whitespace
                excessive_whitespace = str_data.str.contains(r'\s{2,}', regex=True).sum()
                if excessive_whitespace > 0:
                    format_issues.append(f"{excessive_whitespace} entries with excessive whitespace")
                    suggestions.append("Remove extra spaces and normalize whitespace")
                
                # Check for special characters that might indicate encoding issues
                encoding_issues = str_data.str.contains(r'[^\x00-\x7F]', regex=True).sum()
                if encoding_issues > 0:
                    format_issues.append(f"{encoding_issues} entries with special characters")
        
        # Numeric data analysis
        elif col_data.dtype in ['int64', 'float64']:
            detected_type = "numeric"
            # Check for outliers using IQR method
            Q1 = col_data.quantile(0.25)
            Q3 = col_data.quantile(0.75)
            IQR = Q3 - Q1
            outliers = ((col_data < (Q1 - 1.5 * IQR)) | (col_data > (Q3 + 1.5 * IQR))).sum()
            
            if outliers > 0:
                format_issues.append(f"{outliers} potential outliers detected")
                suggestions.append("Review outlier values for data entry errors")
        
        consistency[col] = {
            "invalid_count": int(invalid_count),
            "invalid_percentage": round((invalid_count / len(col_data)) * 100, 2) if len(col_data) > 0 else 0,
            "data_type": detected_type,
            "format_issues": format_issues,
            "suggestions": suggestions,
            "total_valid_entries": len(col_data)
        }
    
    return consistency


def data_profiling(df: pd.DataFrame) -> dict:
    """Comprehensive data profiling with statistical insights"""
    if len(df) == 0:
        return {}
    
    profiling = {}
    
    for col in df.columns:
        col_data = df[col].dropna()
        profile = {
            "column_name": col,
            "data_type": str(df[col].dtype),
            "total_count": len(df),
            "non_null_count": len(col_data),
            "null_count": df[col].isna().sum(),
            "unique_count": df[col].nunique(),
            "duplicate_count": len(col_data) - df[col].nunique()
        }
        
        if len(col_data) > 0:
            # For numeric columns
            if col_data.dtype in ['int64', 'float64']:
                profile.update({
                    "min_value": float(col_data.min()),
                    "max_value": float(col_data.max()),
                    "mean": float(col_data.mean()),
                    "median": float(col_data.median()),
                    "std_dev": float(col_data.std()) if len(col_data) > 1 else 0
                })
            
            # For text columns
            elif col_data.dtype == 'object':
                str_lengths = col_data.astype(str).str.len()
                profile.update({
                    "min_length": int(str_lengths.min()),
                    "max_length": int(str_lengths.max()),
                    "avg_length": round(str_lengths.mean(), 2),
                    "most_common": str(col_data.value_counts().index[0]) if len(col_data) > 0 else "",
                    "most_common_count": int(col_data.value_counts().iloc[0]) if len(col_data) > 0 else 0
                })
        
        profiling[col] = profile
    
    return profiling


def data_quality_score(df: pd.DataFrame) -> dict:
    """Calculate overall data quality score based on multiple factors"""
    if len(df) == 0:
        return {"overall_score": 0, "category": "Poor", "factors": {}}
    
    completeness_data = comp(df)
    duplicates_data = dup(df)
    consistency_data = cons(df)
    
    # Calculate component scores
    completeness_score = sum([col["percentage"] for col in completeness_data.values()]) / len(completeness_data) if completeness_data else 0
    
    duplicate_penalty = duplicates_data["duplicate_percentage"]
    duplicates_score = max(0, 100 - duplicate_penalty)
    
    consistency_scores = []
    for col_data in consistency_data.values():
        col_score = max(0, 100 - col_data["invalid_percentage"])
        consistency_scores.append(col_score)
    consistency_score = sum(consistency_scores) / len(consistency_scores) if consistency_scores else 0
    
    # Weight the scores
    weights = {"completeness": 0.4, "duplicates": 0.3, "consistency": 0.3}
    overall_score = (
        completeness_score * weights["completeness"] +
        duplicates_score * weights["duplicates"] +
        consistency_score * weights["consistency"]
    )
    
    # Categorize quality
    if overall_score >= 90:
        category = "Excellent"
    elif overall_score >= 75:
        category = "Good"
    elif overall_score >= 60:
        category = "Fair"
    elif overall_score >= 40:
        category = "Poor"
    else:
        category = "Critical"
    
    return {
        "overall_score": round(overall_score, 2),
        "category": category,
        "factors": {
            "completeness_score": round(completeness_score, 2),
            "duplicates_score": round(duplicates_score, 2),
            "consistency_score": round(consistency_score, 2)
        },
        "recommendations": get_quality_recommendations(overall_score, duplicates_data["duplicate_percentage"], completeness_score, consistency_score)
    }


def get_quality_recommendations(overall_score, duplicate_pct, completeness_score, consistency_score):
    """Generate actionable recommendations based on quality scores"""
    recommendations = []
    
    if overall_score < 60:
        recommendations.append("Data quality needs immediate attention")
    
    if completeness_score < 80:
        recommendations.append("Address missing data issues - consider data collection improvements")
    
    if duplicate_pct > 5:
        recommendations.append("Implement duplicate detection and removal procedures")
    
    if consistency_score < 70:
        recommendations.append("Standardize data formats and implement validation rules")
    
    if not recommendations:
        recommendations.append("Maintain current data quality standards")
    
    return recommendations


def quality(df: pd.DataFrame) -> dict:
    """Compute comprehensive quality indicators with enhanced metrics"""
    return {
        "completeness": comp(df),
        "duplicates": dup(df),
        "consistency": cons(df),
        "data_profiling": data_profiling(df),
        "quality_score": data_quality_score(df),
        "summary": {
            "total_rows": len(df),
            "total_columns": len(df.columns) if not df.empty else 0,
            "memory_usage": df.memory_usage(deep=True).sum() if not df.empty else 0,
            "analysis_timestamp": pd.Timestamp.now().isoformat()
        }
    }
