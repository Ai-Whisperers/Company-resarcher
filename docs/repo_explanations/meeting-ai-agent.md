# meeting-ai-agent

**Description:** Real-time strategies during meetings
**URL:** https://github.com/Ai-Whisperers/meeting-ai-agent
**Visibility:** PRIVATE

---

# Meetings Agent - B2B Strategy Assistant

> Real-time AI-powered meeting insights using OpenAI's Realtime API

A browser-based application that provides strategic B2B insights during meetings in real-time. The AI acts as your strategic advisor, analyzing conversations and providing actionable insights categorized as Opportunities, Cautions, Risks, and Next Steps.

## Features

- **Real-Time Transcription**: Automatic speech-to-text transcription of meetings
- **Strategic Insights**: AI-powered B2B strategy advice in four categories:
  - 🟢 **Opportunities**: When to emphasize value and pitch solutions
  - 🟡 **Cautions**: Client concerns that need addressing
  - 🔴 **Risks**: Red flags and potential deal-breakers
  - 🔵 **Next Steps**: Concrete action items
- **Audio Capture**: Captures both system audio (other participants) and microphone (you)
- **Meeting History**: Stores meetings locally in browser with export capabilities
- **Clean Interface**: Split-panel dashboard with transcript and insights side-by-side
- **Flexible API Keys**: Supports repository secrets, request body, or header-based API keys

## Architecture

- **Frontend**: React + TypeScript + Vite
- **Backend**: Minimal serverless function for token generation
- **API**: OpenAI Realtime API (WebRTC)
- **Storage**: localStorage (no database required)
- **Deployment**: Vercel (frontend + backend)

## Prerequisites

- Node.js 18+ installed
- OpenAI API key with Realtime API access
- Modern web browser (Chrome, Edge, or Firefox)

## Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd meetings-agent
```

### 2. Backend Setup

```bash
cd backend
npm install
```

Create `.env` file:
```bash
cp .env.example .env
```

Edit `.env` and add your OpenAI API key:
```
OPENAI_API_KEY=sk-proj-your-actual-key-here
```

Start backend:
```bash
npm run dev
```

Backend will run on `http://localhost:3000`

### 3. Frontend Setup

Open a new terminal:

```bash
cd frontend
npm install
```

Create `.env.local` file:
```bash
cp .env.example .env.local
```

Edit `.env.local`:
```
VITE_API_URL=http://localhost:3000
```

Start frontend:
```bash
npm run dev
```

Frontend will run on `http://localhost:5173`

### 4. Use the Application

1. Open `http://localhost:5173` in your browser
2. Click "Start Meeting"
3. Grant permissions:
   - Select screen/window to share
   - **Important**: Check "Share system audio"
   - Allow microphone access
4. Start your meeting (Zoom, Teams, etc.)
5. Watch as transcript and insights appear in real-time

## Deployment

### Deploy Backend to Vercel

```bash
cd backend
npm run deploy
```

Set environment variable in Vercel dashboard:
- `OPENAI_API_KEY`: Your OpenAI API key

Copy the deployed URL (e.g., `https://your-backend.vercel.app`)

### Deploy Frontend to Vercel

Update `frontend/.env.production`:
```
VITE_API_URL=https://your-backend.vercel.app
```

Deploy:
```bash
cd frontend
npm run build
npm run deploy
```

## Project Structure

```
meetings-agent/
├── backend/                     # Serverless backend
│   ├── api/
│   │   └── session.ts          # Token generation endpoint
│   ├── package.json
│   ├── vercel.json
│   └── .env                    # API keys (gitignored)
│
├── frontend/                    # React application
│   ├── src/
│   │   ├── components/         # React components
│   │   │   ├── Dashboard.tsx
│   │   │   ├── TranscriptPanel.tsx
│   │   │   ├── InsightsPanel.tsx
│   │   │   ├── MeetingControls.tsx
│   │   │   └── MeetingHistory.tsx
│   │   ├── services/           # Business logic
│   │   │   ├── audio-capture.ts
│   │   │   ├── realtime-client.ts
│   │   │   ├── session-manager.ts
│   │   │   └── storage-service.ts
│   │   ├── hooks/
│   │   │   └── useRealtimeSession.ts
│   │   ├── types/
│   │   │   └── index.ts
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
│
├── context.md                   # Design documentation
└── README.md
```

## How It Works

1. **Ephemeral Token Generation**:
   - Backend securely generates short-lived tokens from your OpenAI API key
   - Tokens are safe to use in the browser (expire in 1-2 hours)

2. **Audio Capture**:
   - Browser requests screen share permission (with system audio)
   - Microphone permission requested separately
   - Both streams merged using Web Audio API
   - Combined stream sent to OpenAI at 24kHz

3. **Real-Time Processing**:
   - Audio streamed to OpenAI Realtime API via WebRTC
   - AI transcribes speech in real-time
   - AI analyzes conversation for B2B strategic insights
   - Insights categorized and displayed with color coding

4. **Persistence**:
   - Meeting sessions saved to localStorage
   - Export as Markdown or JSON
   - No server storage required

## Configuration

### Backend API Key Options (Priority Order)

1. **Repository Secret**: `OPENAI_API_KEY` environment variable (recommended)
2. **Request Body**: `{ "apiKey": "sk-..." }` in POST body
3. **Request Header**: `X-Api-Key: sk-...` header

### Frontend Environment Variables

- `VITE_API_URL`: Backend URL (default: `http://localhost:3000`)

## Browser Compatibility

- ✅ Chrome 100+
- ✅ Edge 100+
- ✅ Firefox 100+
- ⚠️ Safari (limited support for screen audio capture)

## Troubleshooting

### "Failed to capture system audio"

**Solution**: When sharing screen, make sure to check the "Share system audio" checkbox in the dialog.

### "Failed to connect to backend"

**Solution**:
1. Ensure backend is running (`cd backend && npm run dev`)
2. Check `VITE_API_URL` in `frontend/.env.local`
3. Verify CORS is enabled in backend

### "No audio track in display media stream"

**Solution**: Your browser or OS may not support system audio capture. Try:
1. Use Chrome or Edge (best support)
2. Grant microphone permission (will capture your voice only)

### Ephemeral token expired

**Solution**: Tokens expire after 1-2 hours. Simply end the meeting and start a new one.

## Security Notes

- **API Key Security**: Your OpenAI API key is stored only on the backend
- **Ephemeral Tokens**: Short-lived tokens are used in the browser (safe)
- **Local Storage**: All meeting data stored locally in your browser
- **No Server Storage**: No meeting data is sent to any server except OpenAI

## Cost Considerations

OpenAI Realtime API pricing:
- Audio input: ~$0.06 per minute
- Audio output: ~$0.24 per minute (not used in this app)
- Text input/output: Standard GPT-4 pricing

**Estimated cost**: ~$3.60 per hour of meeting time

## Roadmap

- [ ] Multi-language support
- [ ] Speaker identification
- [ ] Custom insight categories
- [ ] Integration with calendar apps
- [ ] Team collaboration features
- [ ] Advanced analytics dashboard

## Contributing

Contributions welcome! Please read CONTRIBUTING.md for guidelines.

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
- GitHub Issues: [Create an issue](https://github.com/your-repo/issues)
- Documentation: See `context.md` for technical details

## Acknowledgments

- Built with [OpenAI Realtime API](https://platform.openai.com/docs/guides/realtime)
- Uses [@openai/realtime-api-beta](https://www.npmjs.com/package/@openai/realtime-api-beta)
- Inspired by the need for better B2B meeting outcomes

---

**Made with ❤️ for better B2B relationships**
