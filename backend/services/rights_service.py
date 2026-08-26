import uuid
from sqlalchemy.orm import Session
from sqlalchemy import text

def is_valid_uuid(val):
    try:
        uuid.UUID(str(val))
        return True
    except ValueError:
        return False

def get_full_music_rights(recording_id: str, db: Session):
    if not recording_id or not is_valid_uuid(recording_id):
        return {"status": "NOT_FOUND", "message": f"ID không hợp lệ hoặc không đúng định dạng UUID: {recording_id}"}

    query_recording = text("""
        SELECT r.recording_id, r.title AS recording_title, r.artist, r.album, 
               r.release_year, r.duration, r.source_dataset,
               c.composition_id, c.title AS composition_title, c.composer, c.public_domain_status
        FROM recordings r
        LEFT JOIN compositions c ON r.composition_id = c.composition_id
        WHERE r.recording_id = :rec_id
    """)
    
    recording_info = db.execute(query_recording, {"rec_id": recording_id}).fetchone()

    if not recording_info:
        return {"status": "NOT_FOUND", "message": f"Không tìm thấy bản ghi với ID {recording_id}"}

    query_rights = text("""
        SELECT rights_id, license_type, copyright_status, attribution_required,
               commercial_use_allowed, modification_allowed, monetization_allowed,
               revenue_share_required, territory, platform, source_url
        FROM rights
        WHERE recording_id = :rec_id OR composition_id = :comp_id
        LIMIT 1
    """)
    
    rights_info = db.execute(query_rights, {
        "rec_id": recording_id, 
        "comp_id": str(recording_info.composition_id)
    }).fetchone()

    rights_data = {
        "license_type": rights_info.license_type if rights_info else "UNKNOWN",
        "copyright_status": rights_info.copyright_status if rights_info else "PROTECTED",
        "attribution_required": rights_info.attribution_required if rights_info else True,
        "commercial_use_allowed": rights_info.commercial_use_allowed if rights_info else False,
        "monetization_allowed": rights_info.monetization_allowed if rights_info else False,
        "revenue_share_required": rights_info.revenue_share_required if rights_info else False,
        "platform": rights_info.platform if rights_info else "ALL",
        "source_url": rights_info.source_url if rights_info else None
    }

    recommendation = generate_rights_recommendation(rights_data)

    return {
        "status": "SUCCESS",
        "track_metadata": {
            "recording_id": str(recording_info.recording_id),
            "recording_title": recording_info.recording_title,
            "artist": recording_info.artist,
            "album": recording_info.album,
            "release_year": recording_info.release_year,
            "duration": recording_info.duration,
            "source_dataset": recording_info.source_dataset,
            "composition": {
                "composition_id": str(recording_info.composition_id),
                "title": recording_info.composition_title,
                "composer": recording_info.composer,
                "public_domain_status": recording_info.public_domain_status
            }
        },
        "rights_and_licensing": rights_data,
        "usage_recommendation": recommendation
    }

def generate_rights_recommendation(rights: dict) -> str:
    status = rights.get("copyright_status")
    commercial = rights.get("commercial_use_allowed")
    attribution = rights.get("attribution_required")
    rev_share = rights.get("revenue_share_required")

    if status == "PUBLIC_DOMAIN":
        return "Tác phẩm thuộc Miền công cộng (Public Domain). Bạn có thể tự do sử dụng, chỉnh sửa và bật kiếm tiền."
    
    if commercial and not rev_share:
        msg = "Được phép sử dụng cho mục đích thương mại."
        if attribution:
            msg += " Yêu cầu phải ghi công (Attribution) tác giả trong phần mô tả."
        return msg
        
    if rev_share:
        return "Tác phẩm cho phép sử dụng nhưng YÊU CẦU PHÂN CHIA DOANH THU (Revenue Share) theo cơ chế Creator Music."
        
    return "CẢNH BÁO: Bài hát được bảo hộ bản quyền nghiêm ngặt. Không được phép tự ý bật kiếm tiền hoặc thương mại hóa nếu chưa xin giấy phép."