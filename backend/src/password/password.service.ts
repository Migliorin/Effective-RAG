import { Injectable } from '@nestjs/common';
import { randomBytes, scrypt, timingSafeEqual} from 'node:crypto';

@Injectable()
export class PasswordService {
  private readonly saltLength = 16;
  private readonly keyLength = 64;

  constructor(){}

  async hash(password: string): Promise<string> {
    const salt = randomBytes(this.saltLength).toString('hex');

    const derivedKey = await this.deriveKey(password, salt);
    const hash = derivedKey.toString('hex');

    return `${salt}.${hash}`;
  }

  async compare( password: string, storedPasswordHash: string ): Promise<boolean> {
    const [salt, storedHash] = storedPasswordHash.split('.');

    if (!salt || !storedHash) {
      return false;
    }

    // 16 bytes em hexadecimal = 32 caracteres
    const validSalt = /^[a-f0-9]{32}$/i.test(salt);

    // 64 bytes em hexadecimal = 128 caracteres
    const validHash = /^[a-f0-9]{128}$/i.test(storedHash);

    if (!validSalt || !validHash) {
      return false;
    }

    const derivedKey = await this.deriveKey(password, salt);
    const storedKey = Buffer.from(storedHash, 'hex');

    if (derivedKey.length !== storedKey.length) {
      return false;
    }

    return timingSafeEqual(derivedKey, storedKey);
  }

  private deriveKey(password: string, salt: string): Promise<Buffer> {
    return new Promise((resolve, reject) => {
      scrypt(password,salt, this.keyLength,
        (error, derivedKey) => {
          if (error) {
            reject(error);
            return;
          }

          resolve(derivedKey);
        },
      );
    });
  }

}
