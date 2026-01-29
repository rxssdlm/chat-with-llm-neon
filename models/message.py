from sqlalchemy import String, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from core.db import Base ## Base es la clase madre de todos los modelos, le avisa a SQLAlchemy que esta es una tabla.


class Message(Base):
    __tablename__ = "messages" 

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    conversation_id: Mapped[int] = mapped_column( #cada mensaje pertenece a una conversacion
        ForeignKey("conversations.id", ondelete="CASCADE"), #si borran automaticamente borra los mensajes relacionados
        index=True
    )

    role: Mapped[str] = mapped_column(String(20)) #guarda si es user o assistant
    content: Mapped[str] = mapped_column(String) #guarda el contenido del mensaje
    created_at: Mapped[DateTime] = mapped_column( #guarda la fecha de creacion del mensaje
        DateTime(timezone=True),
        server_default=func.now()
    )

#Esta seccion explica que quiero una tabla llamada messages, con un id, 
# un conversation_id que es una clave foranea a la tabla conversations, un role, 
# un content y una fecha de creacion