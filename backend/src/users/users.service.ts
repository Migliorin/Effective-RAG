import { Injectable } from '@nestjs/common';
import { CreateUserDto } from './dto/create-user.dto.js';
import { LoginUserDto } from './dto/login-user.dto.js';
import { PrismaService } from '../prisma/prisma.service.js';
import { userAlreadyExist, invalidCredentials } from './exceptions/user-exceptions.js';
import { PasswordService } from '../password/password.service.js';

@Injectable()
export class UsersService {
  constructor(
    private readonly prismaService: PrismaService,
    private readonly passwordService: PasswordService,
  ){}

  async create(userDto: CreateUserDto):Promise<any> {
    const user = await this.prismaService.user.findFirst({
      where: {email: userDto.email}
    })

    if(user){
      userAlreadyExist()
    }

    const prismaInfo = await this.prismaService.user.create({
      data:{
        ...(userDto),
        password: await this.passwordService.hash(userDto.password)
      }
    })

    return prismaInfo
  }

  async login(userDto: LoginUserDto):Promise<any>{
    const user = await this.prismaService.user.findFirst({
      where: {email: userDto.email}
    })

    if(!user){
      invalidCredentials()
    }

    const valPassword = await this.passwordService.compare(
      userDto.password,
      user.password
    );
    
    if(!valPassword){
      invalidCredentials()
    }
    return user

  }

}
