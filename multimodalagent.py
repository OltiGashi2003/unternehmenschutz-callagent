from dotenv import load_dotenv
from usch_prompts import SYSTEM_PROMPT, EINFUEHRUNG
from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions,function_tool
from livekit.plugins import openai  # Removed noise_cancellation import
#add noice_cancellation later
load_dotenv()

class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)
        

        
async def entrypoint(ctx: agents.JobContext):
    await ctx.connect()

    session = AgentSession(
        llm=openai.realtime.RealtimeModel(voice="shimmer"),
    )

    await session.start(
        room=ctx.room,
        agent=Assistant(),
        room_input_options=RoomInputOptions(
            # Removed noise_cancellation: noise_cancellation.BVC(), or use other options if available.
        ),
    )
    
    @function_tool
    async def on_enter(self) -> None:
        await self.session.generate_reply(instructions=EINFUEHRUNG)
    
    @function_tool
    async def end_call(self) -> None:
        await self.session.generate_reply(
            instructions="Verabschieden Sie sich bitte von dem Benutzer, wenn Sie sich vergewissert haben, dass Sie die richtige E-Mail von ihm erhalten haben, und bevor Sie den Vorgang beenden.",
        )
    

if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))