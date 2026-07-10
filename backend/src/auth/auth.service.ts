import { Injectable } from '@nestjs/common';
import { JwtService } from '@nestjs/jwt';
import { UsersService } from '../users/users.service.js';
import { CreateUserDto } from '../users/dto/create-user.dto.js';
import { CreateTokens } from './dto/create-tokens.dto.js';

@Injectable()
export class AuthService {
  constructor(
    private readonly usersService: UsersService,
    private readonly jwtService: JwtService
  ){}
  

  async register(userDto:CreateUserDto):Promise<CreateTokens>{
    const prismaInfo = await this.usersService.create(userDto)

    const userInfo = {
        email: prismaInfo.email,
        name: prismaInfo.name
    }

    const accessToken = this.jwtService.sign({
      ...userInfo,
      type: 'access',
    });

    const refreshToken = this.jwtService.sign(
      { ...userInfo, type: 'refresh' },
      { expiresIn: "7d" },
    );

  return {
    accessToken: accessToken,
    refreshToken: refreshToken
  }

  }
}
