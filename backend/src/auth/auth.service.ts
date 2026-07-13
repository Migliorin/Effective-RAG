import { Injectable } from '@nestjs/common';
import { JwtService } from '@nestjs/jwt';
import { UsersService } from '../users/users.service.js';
import { CreateUserDto } from '../users/dto/create-user.dto.js';
import { LoginUserDto } from '../users/dto/login-user.dto.js';
import { CreateTokens } from './dto/create-tokens.dto.js';
import { ConfigService } from '@nestjs/config';

@Injectable()
export class AuthService {
  constructor(
    private readonly usersService: UsersService,
    private readonly jwtService: JwtService,
    private readonly config: ConfigService,
  ){}
  

  async register(userDto:CreateUserDto):Promise<CreateTokens>{
    const expiresInRefresh = this.config.getOrThrow("EXPIRES_IN_REFRESH")
    const prismaInfo = await this.usersService.create(userDto)

    const userInfo = {
        email: prismaInfo.email,
        name: prismaInfo.name
    }
  
    return await this.createToken(userInfo,expiresInRefresh);

  }

  async login(userDto: LoginUserDto):Promise<CreateTokens>{
    const expiresInRefresh = this.config.getOrThrow("EXPIRES_IN_REFRESH")
    const prismaInfo = await this.usersService.login(userDto)

    const userInfo = {
        email: prismaInfo.email,
        name: prismaInfo.name
    }


    return await this.createToken(userInfo,expiresInRefresh);
  }

  private createToken(userInfo:any, expires:any): CreateTokens{
    
    const accessToken = this.jwtService.sign({
      ...userInfo,
      type: 'access',
    });

    const refreshToken = this.jwtService.sign(
      { ...userInfo, type: 'refresh' },
      { expiresIn:  expires },
    );

    return {
      accessToken: accessToken,
      refreshToken: refreshToken
    }
  }
}
