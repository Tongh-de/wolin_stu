from sqlalchemy.orm import Session
from model.conversation import ConversationMemory
from typing import List, Optional, Dict, Any


class ConversationService:
    @staticmethod
    def save_turn(db: Session, session_id: str, turn_index: int, question: str, sql_query: Optional[str] = None, result_summary: Optional[str] = None, answer_text: Optional[str] = None, full_data_saved: bool = False, aggregate_sql: Optional[str] = None, embedding_vector: Optional[Dict[str, Any]] = None) -> ConversationMemory:
        record = ConversationMemory(session_id=session_id, turn_index=turn_index, question=question, sql_query=sql_query, result_summary=result_summary, answer_text=answer_text, full_data_saved=full_data_saved, aggregate_sql=aggregate_sql, embedding_vector=embedding_vector)
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def get_recent_turns(db: Session, session_id: str, limit: int = 5) -> List[ConversationMemory]:
        records = db.query(ConversationMemory).filter(ConversationMemory.session_id == session_id).order_by(ConversationMemory.turn_index.desc()).limit(limit).all()
        return list(reversed(records))

    @staticmethod
    def get_latest_turn(db: Session, session_id: str) -> Optional[ConversationMemory]:
        return db.query(ConversationMemory).filter(ConversationMemory.session_id == session_id).order_by(ConversationMemory.turn_index.desc()).first()

    @staticmethod
    def get_turn_count(db: Session, session_id: str) -> int:
        return db.query(ConversationMemory).filter(ConversationMemory.session_id == session_id).count()

    @staticmethod
    def get_previous_sql_turn(db: Session, session_id: str) -> Optional[ConversationMemory]:
        return db.query(ConversationMemory).filter(ConversationMemory.session_id == session_id, ConversationMemory.sql_query.isnot(None)).order_by(ConversationMemory.turn_index.desc()).first()
