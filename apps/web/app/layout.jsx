import "@tabler/core/dist/css/tabler.min.css";
import "@tabler/icons-webfont/dist/tabler-icons.min.css";
import "./globals.css";
import Shell from "./shell";

export const metadata = { title: "IM-VEST Intelligence" };

export default function Layout({ children }) {
  return (
    <html lang="id" data-bs-theme="dark">
      <body>
        <Shell>{children}</Shell>
      </body>
    </html>
  );
}
