import {HttpException, HttpStatus} from '@nestjs/common';

export function invalidToken(){
    throw new HttpException("invalid_token",HttpStatus.UNAUTHORIZED)
}
