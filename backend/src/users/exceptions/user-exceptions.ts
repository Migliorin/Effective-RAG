import {HttpException, HttpStatus} from '@nestjs/common';

export function invalidCredentials():never{
    throw new HttpException("invalid_credentials", HttpStatus.UNAUTHORIZED);
}

export function userAlreadyExist():never{
    throw new HttpException("user_already_exist", HttpStatus.CONFLICT);
}
