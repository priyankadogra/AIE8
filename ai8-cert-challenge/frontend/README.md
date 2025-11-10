# Scout Frontend

Simple React frontend for the Scout school events assistant.

## Getting Started

### Installation

```bash
npm install
```

### Development

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to view the app.

### Build for Production

```bash
npm run build
npm start
```

## Configuration

The frontend connects to the FastAPI backend. Update the API URL in the Settings panel or modify the default in `app/page.tsx`.

## Deploy to Vercel

```bash
vercel
```

Or connect your GitHub repository to Vercel for automatic deployments.

## Features

- 🏫 Clean, simple chat interface
- 🔑 Secure API key management (in-browser only)
- 🧠 Optional Cohere reranking for better results
- ⚙️ Easy configuration panel
- 📱 Responsive design

## Tech Stack

- Next.js 14
- TypeScript
- Tailwind CSS
- React Hooks

