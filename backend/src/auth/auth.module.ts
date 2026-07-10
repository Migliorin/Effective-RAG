import { Module } from '@nestjs/common';
import { AuthService } from './auth.service';
import { UsersService} from  '../users/users.service.js'
import { JwtModule } from '@nestjs/jwt';
import { ConfigService } from '@nestjs/config';
import {PrismaService} from '../prisma/prisma.service.js';
import { AuthController } from './auth.controller';

@Module({
  imports: [
    JwtModule.registerAsync({
      inject: [ConfigService],
      useFactory: (config: ConfigService) => ({
        secret: config.getOrThrow('JWT_SECRET'),
        signOptions: { expiresIn: config.getOrThrow('EXPIRESS_IN') },
      }),
    }),
  ],
  providers: [AuthService, UsersService, ConfigService, PrismaService],
  controllers: [AuthController]
})
export class AuthModule {}
