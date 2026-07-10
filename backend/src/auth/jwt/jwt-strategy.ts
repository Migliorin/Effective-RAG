import {Injectable} from '@nestjs/common';
import {PassportStrategy} from '@nestjs/passport';
import {ExtractJwt, Strategy} from 'passport-jwt';
import {invalidToken} from './execptions/jwt-exceptions.js'
import { ConfigService } from '@nestjs/config';

@Injectable()
export class JwtStrategy extends PassportStrategy(Strategy) {

  constructor(private readonly config: ConfigService){
    super({
      secretOrKey: config.getOrThrow('JWT_SECRET'),
      jwtFromRequest: ExtractJwt.fromAuthHeaderAsBearerToken(),
      ignoreExpiration: false,
      passReqToCallback: true,
    });
  }

  async validate(request: any, payload: any): Promise<any>{
    if (payload.type !== 'access') {
      invalidToken()
    }

    const token = ExtractJwt.fromAuthHeaderAsBearerToken()(request);
  
    return token;
  
  }
}
