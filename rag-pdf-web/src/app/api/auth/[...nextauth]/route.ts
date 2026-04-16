import NextAuth from "next-auth";
import GoogleProvider from "next-auth/providers/google";

const handler = NextAuth({
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID || "",
      clientSecret: process.env.GOOGLE_CLIENT_SECRET || "",
    }),
  ],
  pages: {
    signIn: '/login', // Pointing to our custom glassmorphism login page!
  },
  secret: process.env.NEXTAUTH_SECRET || "fallback_default_secret_123",
});

export { handler as GET, handler as POST };
