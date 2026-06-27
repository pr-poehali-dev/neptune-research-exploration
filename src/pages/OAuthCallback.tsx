import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import func2url from "../../backend/func2url.json";

interface OAuthCallbackProps {
  provider: "vk" | "google";
}

const OAuthCallback = ({ provider }: OAuthCallbackProps) => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [error, setError] = useState("");

  useEffect(() => {
    const code = searchParams.get("code");
    if (!code) {
      setError("Код авторизации не получен");
      return;
    }

    fetch(`${func2url["auth-vk"]}?provider=${provider}&code=${encodeURIComponent(code)}`)
      .then((res) => res.json())
      .then((data) => {
        if (data.error) {
          setError(data.error);
          return;
        }
        localStorage.setItem("session_id", data.session_id);
        localStorage.setItem("user_email", data.email);
        if (data.name) localStorage.setItem("user_name", data.name);
        navigate("/generate");
      })
      .catch(() => setError("Ошибка авторизации. Попробуйте снова."));
  }, []);

  if (error) {
    return (
      <main className="min-h-screen bg-background flex items-center justify-center px-4">
        <div className="text-center">
          <p className="text-destructive mb-4">{error}</p>
          <a href="/login" className="text-primary hover:underline">
            Вернуться к входу
          </a>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-background flex items-center justify-center px-4">
      <div className="text-center text-muted-foreground">
        <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4" />
        Выполняется вход...
      </div>
    </main>
  );
};

export default OAuthCallback;
