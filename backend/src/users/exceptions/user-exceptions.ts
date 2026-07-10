import {HttpException, HttpStatus} from '@nestjs/common';

export function invalidCredentials(){
    throw new HttpException("invalid_credentials", HttpStatus.UNAUTHORIZED);
}

export function userAlreadyExist(){
    throw new HttpException("user_already_exist", HttpStatus.CONFLICT);
}
