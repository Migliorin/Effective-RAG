import { Module } from '@nestjs/common';
import { PrismaService } from './prisma.service.js'
import { ConfigService } from '@nestjs/config';

@Module({
  providers: [PrismaService, ConfigService],
  controllers: [],
  exports: [PrismaService],
})
export class PrismaModule {}
