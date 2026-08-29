def evaluate_rights_and_risk(rights_data: dict, match_info: dict) -> dict:
    license_type = rights_data.get("license_type", "UNKNOWN")
    copyright_status = rights_data.get("copyright_status", "UNKNOWN")
    attribution_req = rights_data.get("attribution_required", True)
    commercial_allowed = rights_data.get("commercial_use_allowed", False)
    revenue_share_req = rights_data.get("revenue_share_required", False)
    
    # 1. Nhóm Audio Library
    if license_type == "AUDIO_LIBRARY":
        return {
            "category": "AUDIO_LIBRARY",
            "risk_level": "LOW" if not attribution_req else "CONDITIONAL",
            "condition": "FREE_TO_USE" if not attribution_req else "ATTRIBUTION_REQUIRED"
        }
    
    # 2. Nhóm Creator Music
    elif license_type == "CREATOR_MUSIC":
        return {
            "category": "CREATOR_MUSIC",
            "risk_level": "CONDITIONAL",
            "condition": "REVENUE_SHARE_APPLIED" if revenue_share_req else "LICENSE_REQUIRED"
        }
        
    # 3. Nhóm Content ID / Thương mại
    elif license_type in ["COMMERCIAL", "CONTENT_ID"]:
        return {
            "category": "COMMERCIAL_CONTENT_ID",
            "risk_level": "HIGH",
            "condition": "MONETIZATION_BLOCKED_OR_CLAIMED"
        }

    # 4. Nhóm Creative Commons
    elif "CC" in license_type:
        risk = "CONDITIONAL" if commercial_allowed else "HIGH"
        return {
            "category": "CREATIVE_COMMONS",
            "risk_level": risk,
            "condition": "ATTRIBUTION_REQUIRED"
        }

    # 5. Nhóm Public Domain
    elif copyright_status == "PUBLIC_DOMAIN":
        return {
            "category": "PUBLIC_DOMAIN",
            "risk_level": "LOW",
            "condition": "NONE"
        }

    # Nhóm ngoại lệ / Không rõ
    return {
        "category": "UNCATEGORIZED",
        "risk_level": "UNKNOWN",
        "condition": "HUMAN_REVIEW_REQUIRED"
    }