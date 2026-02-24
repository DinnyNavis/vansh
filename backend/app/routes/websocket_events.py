import logging
from flask import current_app, request
from flask_socketio import join_room, leave_room
from ..extensions import socketio
from ..services.deepgram_service import DeepgramService

logger = logging.getLogger(__name__)

# Track active streaming connections: { sid: dg_connection }
streaming_connections = {}

@socketio.on("connect")
def handle_connect():
    """Handle client connection."""
    logger.info(f"Client connected: {request.sid}")


@socketio.on("disconnect")
def handle_disconnect():
    """Handle client disconnection and cleanup streaming."""
    sid = request.sid
    logger.info(f"Client disconnected: {sid}")
    if sid in streaming_connections:
        try:
            streaming_connections[sid].finish()
            del streaming_connections[sid]
        except Exception as e:
            logger.error(f"Error cleaning up streaming on disconnect: {e}")


@socketio.on("join_project")
def handle_join_project(data):
    """Join a project room for receiving updates."""
    project_id = data.get("project_id")
    if project_id:
        join_room(project_id)
        logger.info(f"Client {request.sid} joined project room: {project_id}")


@socketio.on("leave_project")
def handle_leave_project(data):
    """Leave a project room."""
    project_id = data.get("project_id")
    if project_id:
        leave_room(project_id)
        logger.info(f"Client {request.sid} left project room: {project_id}")


@socketio.on("start_transcription")
def handle_start_transcription(data):
    """Initialize a Deepgram live session."""
    sid = request.sid
    project_id = data.get("project_id")
    
    if not project_id:
        return {"error": "project_id is required"}

    logger.info(f"Starting real-time transcription for SID: {sid}, Project: {project_id}")
    
    api_key = current_app.config.get("DEEPGRAM_API_KEY")
    if not api_key:
        logger.error("DEEPGRAM_API_KEY not found in config")
        return {"error": "Transcription service not configured"}

    def on_message(transcript, is_final=False):
        # Emit the transcript to the specific project room
        socketio.emit("realtime_transcript", {
            "transcript": transcript,
            "is_final": is_final,
            "project_id": project_id
        }, room=project_id)

    try:
        dg_service = DeepgramService(api_key)
        dg_connection = dg_service.start_live_transcription(on_message=on_message)
        streaming_connections[sid] = dg_connection
        return {"status": "started"}
    except Exception as e:
        logger.error(f"Failed to start streaming: {e}")
        return {"error": str(e)}


@socketio.on("audio_chunk")
def handle_audio_chunk(data):
    """Receive and forward audio binary data to Deepgram."""
    sid = request.sid
    if sid not in streaming_connections:
        return

    try:
        # data is expected to be binary audio
        streaming_connections[sid].send(data)
    except Exception as e:
        logger.error(f"Error sending audio to Deepgram for SID {sid}: {e}")
        # Possibly cleanup if connection is totally dead
        if "finished" in str(e).lower() or "closed" in str(e).lower():
            streaming_connections.pop(sid, None)


@socketio.on("stop_transcription")
def handle_stop_transcription(data):
    """Finalize the Deepgram session."""
    sid = request.sid
    if sid in streaming_connections:
        try:
            streaming_connections[sid].finish()
            del streaming_connections[sid]
            logger.info(f"Stopped real-time transcription for SID: {sid}")
            return {"status": "stopped"}
        except Exception as e:
            logger.error(f"Error stopping transcription: {e}")
            return {"error": str(e)}
