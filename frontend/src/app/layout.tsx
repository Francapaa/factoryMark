import type { Metadata } from "next";
import { Space_Grotesk, Inter } from "next/font/google";
import type { ReactNode } from "react";
import "./globals.css";

const display = Space_Grotesk({
  variable: "--font-display",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

const body = Inter({
  variable: "--font-body",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "FactoryMark · Tu espía legal de la competencia",
  description:
    "Investigamos tu competencia local, detectamos oportunidades reales en reviews y te dejamos el post listo para publicar. Para cafés, barberías y pizzerías de barrio.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html
      lang="es"
      className={`${display.variable} ${body.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-[#0A0A0B] text-zinc-100">
        {children}
      </body>
    </html>
  );
}
