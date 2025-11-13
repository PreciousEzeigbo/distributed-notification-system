import { Entity, Column, PrimaryGeneratedColumn } from 'typeorm';

@Entity()
export class User {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column({ unique: true })
  email: string;

  @Column({ nullable: true })
  password: string;

  @Column({ nullable: true })
  push_token: string;

  @Column({ type: 'jsonb', default: { email: true, push: true } })
  preferences: {
    email: boolean;
    push: boolean;
  };
}
