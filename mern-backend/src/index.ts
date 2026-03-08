import express from "express";
import cors from "cors";
import morgan from "morgan";
import mongoose from "mongoose";
import { config } from "./config";
import { transactionRouter } from "./routes/transactions";
import { workflowRouter } from "./routes/workflows";

async function bootstrap() {
  await mongoose.connect(config.mongoUri);

  const app = express();

  app.use(cors());
  app.use(express.json());
  app.use(morgan("dev"));

  app.get("/health", (_req, res) => {
    res.json({ status: "ok", service: "financial-workflow-backend" });
  });

  app.use("/api/transactions", transactionRouter);
  app.use("/api/workflows", workflowRouter);

  app.use((err: unknown, _req: express.Request, res: express.Response, _next: express.NextFunction) => {
    console.error(err);
    res.status(500).json({ error: "Internal server error" });
  });

  app.listen(config.port, () => {
    console.log(`Financial workflow API listening on port ${config.port}`);
  });
}

bootstrap().catch((err) => {
  console.error("Failed to start server", err);
  process.exit(1);
});

