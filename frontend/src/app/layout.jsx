import "./globals.css";

export const metadata = {
  title: "AI Debate Arena — Real-Time Audience Powered Debates",
  description: "Watch open-weight AI agents argue in real-time with live citations and interactive audience voting.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      </head>
      <body>
        <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
          {children}
        </div>
      </body>
    </html>
  );
}
