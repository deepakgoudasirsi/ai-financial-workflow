import dotenv from "dotenv";

dotenv.config();

export const config = {
  port: process.env.PORT ? Number(process.env.PORT) : 4000,
  mongoUri: process.env.MONGO_URI || "mongodb://localhost:27017/financial_workflows",
  openAiApiKey: process.env.OPENAI_API_KEY || "",
  openAiModel: process.env.OPENAI_MODEL || "gpt-4.1-mini"
};

if (!config.mongoUri) {
  // Minimal logging; real app would use logger
  console.warn("MONGO_URI is not set. Using default local MongoDB URL.");
}

