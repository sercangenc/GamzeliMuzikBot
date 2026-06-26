const commands: { cmd: string; alias: string; desc: string }[] = [
  { cmd: "/play", alias: "/oynat, /çal", desc: "Sesli sohbete katıl ve çal" },
  { cmd: "/skip", alias: "/atla, /geç", desc: "Sonraki şarkıya geç" },
  { cmd: "/pause", alias: "/duraklat", desc: "Duraklat" },
  { cmd: "/resume", alias: "/devam", desc: "Devam et" },
  { cmd: "/stop", alias: "/durdur, /dur", desc: "Durdur ve ayrıl" },
  { cmd: "/queue", alias: "/sıra, /kuyruk", desc: "Sırayı göster" },
  { cmd: "/help", alias: "/yardım, /start", desc: "Yardım mesajı" },
];

function App() {
  return (
    <div
      style={{
        minHeight: "100vh",
        width: "100%",
        background: "radial-gradient(circle at 50% 0%, #1d2230 0%, #0b0d12 60%)",
        color: "#e8eaf0",
        fontFamily:
          "Inter, system-ui, -apple-system, Segoe UI, Roboto, sans-serif",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        padding: "3rem 1.25rem 4rem",
        boxSizing: "border-box",
      }}
    >
      <div style={{ fontSize: "3.5rem", lineHeight: 1, marginBottom: "0.75rem" }}>
        🎵
      </div>
      <h1
        style={{
          fontSize: "1.9rem",
          fontWeight: 700,
          margin: "0 0 0.5rem",
          textAlign: "center",
        }}
      >
        Telegram Müzik Botu
      </h1>
      <div
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: "0.5rem",
          padding: "0.35rem 0.9rem",
          borderRadius: "999px",
          background: "rgba(54, 211, 153, 0.12)",
          border: "1px solid rgba(54, 211, 153, 0.35)",
          color: "#36d399",
          fontSize: "0.9rem",
          fontWeight: 600,
          marginBottom: "2.25rem",
        }}
      >
        <span
          style={{
            width: "9px",
            height: "9px",
            borderRadius: "50%",
            background: "#36d399",
            boxShadow: "0 0 10px #36d399",
          }}
        />
        Bot aktif
      </div>

      <div
        style={{
          width: "100%",
          maxWidth: "560px",
          background: "rgba(255, 255, 255, 0.03)",
          border: "1px solid rgba(255, 255, 255, 0.08)",
          borderRadius: "16px",
          padding: "1.5rem",
          boxShadow: "0 20px 50px rgba(0, 0, 0, 0.45)",
        }}
      >
        <h2
          style={{
            fontSize: "0.8rem",
            textTransform: "uppercase",
            letterSpacing: "0.08em",
            color: "#8b93a7",
            margin: "0 0 1rem",
          }}
        >
          Komutlar
        </h2>
        <div style={{ display: "flex", flexDirection: "column", gap: "0.65rem" }}>
          {commands.map((c) => (
            <div
              key={c.cmd}
              style={{
                display: "flex",
                alignItems: "baseline",
                gap: "0.75rem",
                flexWrap: "wrap",
              }}
            >
              <code
                style={{
                  fontFamily: "Menlo, Consolas, monospace",
                  fontSize: "0.92rem",
                  color: "#7eb6ff",
                  fontWeight: 600,
                  minWidth: "72px",
                }}
              >
                {c.cmd}
              </code>
              <span style={{ fontSize: "0.92rem", color: "#cdd2de", flex: 1 }}>
                {c.desc}
              </span>
              <span style={{ fontSize: "0.78rem", color: "#6b7283" }}>
                {c.alias}
              </span>
            </div>
          ))}
        </div>
      </div>

      <p
        style={{
          marginTop: "2rem",
          fontSize: "0.85rem",
          color: "#6b7283",
          textAlign: "center",
          maxWidth: "480px",
          lineHeight: 1.6,
        }}
      >
        Botu Telegram grubunuza ekleyip sesli sohbet başlatın, ardından{" "}
        <code style={{ color: "#7eb6ff" }}>/play şarkı adı</code> yazarak müzik
        çalmaya başlayın.
      </p>
    </div>
  );
}

export default App;
