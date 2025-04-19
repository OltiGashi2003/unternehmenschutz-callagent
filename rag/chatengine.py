from collections.abc import AsyncIterable
from pathlib import Path

from dotenv import load_dotenv
from llama_index.core import (
    SimpleDirectoryReader,
    StorageContext,
    VectorStoreIndex,
    load_index_from_storage,
)
from llama_index.core.chat_engine.types import ChatMode
from llama_index.core.llms import ChatMessage, MessageRole
from rag.prompts import SYSTEM_PROMPT, EINFUEHRUNG
from livekit.agents import Agent, AgentSession, AutoSubscribe, JobContext, WorkerOptions, cli, llm
from livekit.plugins import openai, silero, deepgram,cartesia  # Added silero and deepgram imports

load_dotenv()

# check if storage already exists
THIS_DIR = Path(__file__).parent
PERSIST_DIR = THIS_DIR / "chat-engine-storage"
if not PERSIST_DIR.exists():
    # load the documents and create the index
    documents = SimpleDirectoryReader(THIS_DIR / "data").load_data()
    index = VectorStoreIndex.from_documents(documents)
    # store it for later
    index.storage_context.persist(persist_dir=PERSIST_DIR)
else:
    # load the existing index
    storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
    index = load_index_from_storage(storage_context)


class ChatEngineAgent(Agent):
    def __init__(self, index: VectorStoreIndex):
        super().__init__(
            instructions=SYSTEM_PROMPT,
            vad=silero.VAD.load(),             # Added voice activity detection
            stt=deepgram.STT(),                # Added speech-to-text
            llm=openai.LLM(model="gpt-4"),     # OpenAI LLM for agent reasoning
            tts=cartesia.TTS(voice="alloy", language="de")  # Added TTS with German language
        )
        
        # Configure RAG with OpenAI
        from llama_index.llms.openai import OpenAI
        openai_llm = OpenAI(model="gpt-4")  
        
        self.chat_engine = index.as_chat_engine(
            chat_mode=ChatMode.CONTEXT,
            llm=openai_llm
        )

    async def llm_node(
        self,
        chat_ctx: llm.ChatContext,
        tools: list[llm.FunctionTool],
    ) -> AsyncIterable[str]:  # Removed model_settings parameter
        user_msg = chat_ctx.items.pop()
        assert isinstance(user_msg, llm.ChatMessage) and user_msg.role == "user"
        user_query = user_msg.text_content
        assert user_query is not None

        llama_chat_messages = [
            ChatMessage(content=msg.text_content, role=MessageRole(msg.role))
            for msg in chat_ctx.items
            if isinstance(msg, llm.ChatMessage)
        ]

        stream = await self.chat_engine.astream_chat(user_query, chat_history=llama_chat_messages)
        async for delta in stream.async_response_gen():
            yield delta


async def entrypoint(ctx: JobContext):
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    agent = ChatEngineAgent(index)
    # Don't override the agent's TTS
    session = AgentSession()
    await session.start(agent=agent, room=ctx.room)

    await session.say(EINFUEHRUNG, allow_interruptions=True)


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))