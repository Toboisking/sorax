const stage = process.env.SST_STAGE || "dev"

export default {
  url: stage === "production" ? "https://sorax.ai" : `https://${stage}.sorax.ai`,
  console: stage === "production" ? "https://sorax.ai/auth" : `https://${stage}.sorax.ai/auth`,
  email: "help@anoma.ly",
  socialCard: "https://social-cards.sst.dev",
  github: "https://github.com/anomalyco/sorax",
  discord: "https://sorax.ai/discord",
  headerLinks: [
    { name: "app.header.home", url: "/" },
    { name: "app.header.docs", url: "/v2/docs" },
  ],
}
