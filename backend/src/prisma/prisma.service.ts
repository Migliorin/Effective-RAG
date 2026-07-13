import { Injectable } from '@nestjs/common';
import { PrismaClient } from '../generated/prisma/client.js'
import { PrismaPg } from '@prisma/adapter-pg';
import { ConfigService } from '@nestjs/config';

@Injectable()
export class PrismaService extends PrismaClient {
  constructor(
    private readonly config: ConfigService
  ){
    const adapter = new PrismaPg({
      connectionString: config.getOrThrow("DATABASE_URL"),
    });

    super({adapter});
  }

}
