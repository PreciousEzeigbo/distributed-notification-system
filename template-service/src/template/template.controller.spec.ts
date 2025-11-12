import { Test, TestingModule } from '@nestjs/testing';
import { TemplateController } from './template.controller';
import { TemplateService } from './template.service';
import { getRepositoryToken } from '@nestjs/typeorm';
import { Template } from './template.entity';

describe('TemplateController', () => {
  let controller: TemplateController;
  let service: TemplateService;

  const mockTemplateRepository = {
    find: jest.fn(),
    findOne: jest.fn(),
    create: jest.fn(),
    save: jest.fn(),
    update: jest.fn(),
    delete: jest.fn(),
  };

  const mockTemplateService = {
    findAll: jest.fn(),
    findOne: jest.fn(),
    findByCode: jest.fn(),
    create: jest.fn(),
    update: jest.fn(),
    remove: jest.fn(),
    render: jest.fn(),
  };

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      controllers: [TemplateController],
      providers: [
        {
          provide: TemplateService,
          useValue: mockTemplateService,
        },
        {
          provide: getRepositoryToken(Template),
          useValue: mockTemplateRepository,
        },
      ],
    }).compile();

    controller = module.get<TemplateController>(TemplateController);
    service = module.get<TemplateService>(TemplateService);
  });

  it('should be defined', () => {
    expect(controller).toBeDefined();
  });

  describe('findAll', () => {
    it('should return an array of templates', async () => {
      const result = [{ id: '1', name: 'Test Template' }];
      mockTemplateService.findAll.mockResolvedValue(result);

      expect(await controller.findAll()).toBe(result);
      expect(mockTemplateService.findAll).toHaveBeenCalled();
    });
  });

  describe('findOne', () => {
    it('should return a single template', async () => {
      const result = { id: '1', name: 'Test Template' };
      mockTemplateService.findOne.mockResolvedValue(result);

      expect(await controller.findOne('1')).toBe(result);
      expect(mockTemplateService.findOne).toHaveBeenCalledWith('1');
    });
  });

  describe('findByCode', () => {
    it('should return a template by code', async () => {
      const result = { id: '1', code: 'welcome_email', name: 'Welcome Email' };
      mockTemplateService.findByCode.mockResolvedValue(result);

      expect(await controller.findByCode('welcome_email')).toBe(result);
      expect(mockTemplateService.findByCode).toHaveBeenCalledWith('welcome_email');
    });
  });

  describe('create', () => {
    it('should create a new template', async () => {
      const createDto = {
        name: 'Test Template',
        code: 'test_template',
        subject: 'Test Subject',
        body: 'Test Body',
        type: 'email',
        language: 'en',
      };
      const result = { id: '1', ...createDto };
      mockTemplateService.create.mockResolvedValue(result);

      expect(await controller.create(createDto)).toBe(result);
      expect(mockTemplateService.create).toHaveBeenCalledWith(createDto);
    });
  });
});
