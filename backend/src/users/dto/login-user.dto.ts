import { IsEmail, IsNotEmpty, IsString,} from 'class-validator';
import { ApiProperty } from '@nestjs/swagger';

export class LoginUserDto {
  @ApiProperty({
    description: 'E-mail utilizado para autenticação',
    example: 'lucas@email.com',
    format: 'email',
  })
  @IsNotEmpty()
  @IsEmail()
  readonly email!: string;

  @ApiProperty({
    description: 'Senha da conta',
    example: 'Senha@123',
    writeOnly: true,
  })
  @IsNotEmpty()
  @IsString()
  readonly password!: string;

}
