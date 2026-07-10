import { Controller, Body, Post } from '@nestjs/common';
import {CreateUserDto} from '../users/dto/create-user.dto.js'
import {AuthService} from './auth.service.js';
import {CreateTokens} from './dto/create-tokens.dto.js';

@Controller('auth')
export class AuthController {
  constructor(
    private readonly authService: AuthService,
  ){}
  
  @Post("register")
  async register(@Body() createUserDto: CreateUserDto):Promise<CreateTokens>{
    return await this.authService.register(createUserDto);
  }

}
