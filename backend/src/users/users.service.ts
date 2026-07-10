import { Injectable } from '@nestjs/common';
import { CreateUserDto } from './dto/create-user.dto.js'
import { PrismaService } from '../prisma/prisma.service.js'
import { userAlreadyExist } from './exceptions/user-exceptions.js'

@Injectable()
export class UsersService {
  constructor(
    private readonly prismaService: PrismaService
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
        ...(userDto)
      }
    })

    return prismaInfo
  }

}
