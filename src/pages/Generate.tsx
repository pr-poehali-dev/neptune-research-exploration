import { useState } from "react";
import { Link } from "react-router-dom";
import Icon from "@/components/ui/icon";
import func2url from "../../backend/func2url.json";

const Generate = () => {
  const [prompt, setPrompt] = useState("");
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const userEmail = localStorage.getItem("user_email");

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim()) return;
    setError("");
    setLoading(true);
    setImageUrl(null);

    const res = await fetch(func2url["generate-image"], {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt }),
    });

    const data = await res.json();
    setLoading(false);

    if (!res.ok) {
      setError(data.error || "Ошибка генерации. Попробуйте ещё раз.");
      return;
    }

    setImageUrl(data.url);
  };

  const handleDownload = () => {
    if (!imageUrl) return;
    const a = document.createElement("a");
    a.href = imageUrl;
    a.download = "generated-image.png";
    a.target = "_blank";
    a.click();
  };

  return (
    <main className="min-h-screen bg-background">
      <header className="border-b border-border px-6 py-4 flex items-center justify-between">
        <Link to="/" className="font-bold text-foreground text-lg tracking-tight">
          AI Image
        </Link>
        <div className="flex items-center gap-3">
          {userEmail && (
            <span className="text-sm text-muted-foreground hidden sm:block">{userEmail}</span>
          )}
          <Link to="/" className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors">
            <Icon name="ArrowLeft" size={15} />
            На главную
          </Link>
        </div>
      </header>

      <div className="max-w-4xl mx-auto px-6 py-10">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-foreground">Генератор изображений</h1>
          <p className="mt-2 text-muted-foreground">Опишите, что хотите увидеть — ИИ создаст изображение за секунды</p>
        </div>

        <form onSubmit={handleGenerate} className="flex flex-col gap-4">
          <div className="relative">
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Например: закат над горами в стиле аниме, яркие цвета, детализированно..."
              rows={4}
              className="w-full px-4 py-4 rounded-2xl border border-border bg-card text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all resize-none text-sm"
            />
            <span className="absolute bottom-3 right-4 text-xs text-muted-foreground">{prompt.length} симв.</span>
          </div>

          {error && (
            <p className="text-sm text-destructive bg-destructive/10 px-4 py-3 rounded-xl">{error}</p>
          )}

          <button
            type="submit"
            disabled={loading || !prompt.trim()}
            className="flex items-center justify-center gap-2 w-full sm:w-auto sm:self-end px-8 py-3 rounded-xl bg-primary text-primary-foreground hover:bg-primary/90 transition-all duration-200 font-medium shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 disabled:opacity-60 disabled:cursor-not-allowed disabled:transform-none"
          >
            {loading ? (
              <>
                <Icon name="Loader2" size={18} className="animate-spin" />
                Генерирую...
              </>
            ) : (
              <>
                <Icon name="Sparkles" size={18} />
                Сгенерировать
              </>
            )}
          </button>
        </form>

        {loading && (
          <div className="mt-10 flex flex-col items-center justify-center gap-4 py-20 border border-border rounded-2xl bg-card">
            <div className="w-12 h-12 rounded-full border-4 border-primary/20 border-t-primary animate-spin" />
            <p className="text-muted-foreground text-sm">Создаю изображение, это займёт ~15 секунд...</p>
          </div>
        )}

        {imageUrl && !loading && (
          <div className="mt-10">
            <div className="rounded-2xl overflow-hidden border border-border shadow-xl">
              <img src={imageUrl} alt={prompt} className="w-full object-contain max-h-[600px]" />
            </div>
            <div className="mt-4 flex flex-col sm:flex-row gap-3">
              <button
                onClick={handleDownload}
                className="flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-primary text-primary-foreground hover:bg-primary/90 transition-all font-medium"
              >
                <Icon name="Download" size={18} />
                Скачать
              </button>
              <button
                onClick={() => { setImageUrl(null); setPrompt(""); }}
                className="flex items-center justify-center gap-2 px-6 py-3 rounded-xl border border-border hover:bg-accent transition-all text-foreground"
              >
                <Icon name="RefreshCw" size={18} />
                Новое изображение
              </button>
            </div>
          </div>
        )}
      </div>
    </main>
  );
};

export default Generate;
