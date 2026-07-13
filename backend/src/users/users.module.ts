import { Module } from '@nestjs/common';
import { UsersService } from './users.service.js';
import { PrismaModule } from '../prisma/prisma.module.js';
import { PasswordModule } from '../password/password.module.js';

@Module({
  providers: [UsersService],
  imports: [PrismaModule, PasswordModule],
  controllers: [],
  exports: [UsersService],
})
export class UsersModule {}
