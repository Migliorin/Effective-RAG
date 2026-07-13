import { ApiProperty } from '@nestjs/swagger';

export class CreateTokens {
  @ApiProperty({
    description: 'Token JWT utilizado para autenticar as requisições',
    example: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
    readOnly: true,
  })
  readonly accessToken!: string;

  @ApiProperty({
    description: 'Token utilizado para renovar o access token',
    example: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
    readOnly: true,
  })
  readonly refreshToken!: string;
}
