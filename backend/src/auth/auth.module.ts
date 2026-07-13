import { Module } from '@nestjs/common';
import { AuthService } from './auth.service';
import { UsersModule } from  '../users/users.module.js';
import { JwtModule } from '@nestjs/jwt';
import { ConfigService } from '@nestjs/config';
import { AuthController } from './auth.controller.js';

@Module({
  imports: [
    JwtModule.registerAsync({
      inject: [ConfigService],
      useFactory: (config: ConfigService) => ({
        secret: config.getOrThrow('JWT_SECRET'),
        signOptions: { expiresIn: config.getOrThrow('EXPIRESS_IN') },
      }),
    }),
    UsersModule,
  ],
  providers: [AuthService],
  controllers: [AuthController]
})
export class AuthModule {}
