from skills.knowledge_layer.database import SessionLocal, UserMemoryOverride

def get_all_overrides() -> dict:
    """
    Fetches all user memory overrides from the database and formats them
    into the dictionary structure expected by the pipeline.
    """
    db = SessionLocal()
    try:
        overrides = db.query(UserMemoryOverride).all()
        result = {}
        for override in overrides:
            result[override.clean_desc] = {
                "merchant_name": override.merchant_name,
                "transaction_type": override.transaction_type,
                "category": override.category,
                "sub_category": override.sub_category
            }
        return result
    finally:
        db.close()

def upsert_override(clean_desc: str, merchant_name: str, transaction_type: str, category: str, sub_category: str):
    """
    Inserts a new override or updates an existing one for the given clean_desc.
    """
    db = SessionLocal()
    try:
        override = db.query(UserMemoryOverride).filter(UserMemoryOverride.clean_desc == clean_desc).first()
        if override:
            override.merchant_name = merchant_name
            override.transaction_type = transaction_type
            override.category = category
            override.sub_category = sub_category
        else:
            override = UserMemoryOverride(
                clean_desc=clean_desc,
                merchant_name=merchant_name,
                transaction_type=transaction_type,
                category=category,
                sub_category=sub_category
            )
            db.add(override)
        db.commit()
    finally:
        db.close()
