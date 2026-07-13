import { Controller, Body, Post } from '@nestjs/common';
import { CreateUserDto } from '../users/dto/create-user.dto.js';
import { LoginUserDto } from '../users/dto/login-user.dto.js';
import { AuthService } from './auth.service.js';
import { CreateTokens } from './dto/create-tokens.dto.js';
import {
  ApiCreatedResponse,
  ApiOperation,
  ApiTags,
} from '@nestjs/swagger';


@ApiTags('auth')
@Controller('auth')
export class AuthController {
  constructor(
    private readonly authService: AuthService,
  ) {}

  @Post('register')
  @ApiOperation({
    summary: 'Registra um novo usuário',
  })
  @ApiCreatedResponse({
    description: 'Usuário registrado com sucesso',
    type: CreateTokens,
  })
  async register(@Body() createUserDto: CreateUserDto): Promise<CreateTokens> {
    return await this.authService.register(createUserDto);
  }


  @Post('login')
  @ApiOperation({
    summary: 'Loga com um usuário existente',
  })
  @ApiCreatedResponse({
    description: 'Usuário logado com sucesso',
    type: CreateTokens,
  })
  async login(@Body() loginUserDto: LoginUserDto): Promise<CreateTokens> {
    return await this.authService.login(loginUserDto);
  }
}
