import "./globals.css";
import type {Metadata} from "next";
import type {ReactNode} from "react";

export const metadata: Metadata = {
  title: "CapCutAI Frontend",
  description: "IM workspace scaffold for CapCutAI"
};

export default function RootLayout({children}: {children: ReactNode}) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
