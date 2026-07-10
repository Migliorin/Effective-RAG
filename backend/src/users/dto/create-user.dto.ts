import {IsString, IsNotEmpty, IsEmail} from 'class-validator';

export class CreateUserDto{
  
  @IsNotEmpty()
  @IsEmail()
  readonly email!: string;

  @IsNotEmpty()
  @IsString()
  readonly password!: string;

  @IsNotEmpty()
  @IsString()
  readonly name!: string;

}
