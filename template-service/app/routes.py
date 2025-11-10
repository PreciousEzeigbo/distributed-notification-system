from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List, Optional
from . import models, schemas
from .database import get_db
from .template_renderer import render_template
from .utils.logging_config import setup_logging

logger = setup_logging("template-service")

router = APIRouter()

@router.post("/", response_model=schemas.APIResponse[schemas.TemplateResponse], status_code=status.HTTP_201_CREATED)
def create_template(template: schemas.TemplateCreate, db: Session = Depends(get_db)):
    """Create a new template"""
    logger.info(f"Attempting to create template: {template.name}")
    
    # Check if template name already exists
    existing = db.query(models.Template).filter(models.Template.name == template.name).first()
    if existing:
        logger.warning(f"Template name already exists: {template.name}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Template with name '{template.name}' already exists"
        )
    
    # Create template
    db_template = models.Template(
        name=template.name,
        channel=template.channel,
        language=template.language,
        subject=template.subject,
        body=template.body,
        variables=template.variables
    )
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    
    # Create first version
    version = models.TemplateVersion(
        template_id=db_template.id,
        version=1,
        subject=template.subject,
        body=template.body,
        variables=template.variables
    )
    db.add(version)
    db.commit()
    
    logger.info(f"Template created successfully: {template.name}")
    return schemas.APIResponse(data=db_template, message="Template created successfully")

@router.get("/", response_model=schemas.APIResponse[List[schemas.TemplateResponse]])
def list_templates(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    channel: Optional[str] = None,
    language: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """List all templates with optional filters"""
    query = db.query(models.Template)
    
    if channel:
        query = query.filter(models.Template.channel == channel)
    if language:
        query = query.filter(models.Template.language == language)
    if is_active is not None:
        query = query.filter(models.Template.is_active == is_active)
    
    total = query.count()
    templates = query.offset(skip).limit(limit).all()
    
    # Calculate pagination meta
    total_pages = (total + limit - 1) // limit
    current_page = (skip // limit) + 1
    
    meta = schemas.PaginationMeta(
        total=total,
        limit=limit,
        page=current_page,
        total_pages=total_pages,
        has_next=current_page < total_pages,
        has_previous=current_page > 1
    )
    
    return schemas.APIResponse(
        data=templates,
        message="Templates retrieved successfully",
        meta=meta
    )

@router.get("/{template_id}", response_model=schemas.APIResponse[schemas.TemplateResponse])
def get_template(template_id: int, db: Session = Depends(get_db)):
    """Get template by ID"""
    template = db.query(models.Template).filter(models.Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    return schemas.APIResponse(data=template, message="Template retrieved successfully")

@router.get("/name/{template_name}", response_model=schemas.APIResponse[schemas.TemplateResponse])
def get_template_by_name(template_name: str, language: str = "en", db: Session = Depends(get_db)):
    """Get template by name and language"""
    template = db.query(models.Template).filter(
        models.Template.name == template_name,
        models.Template.language == language
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template '{template_name}' not found for language '{language}'"
        )
    
    return schemas.APIResponse(data=template, message="Template retrieved successfully")

@router.put("/{template_id}", response_model=schemas.APIResponse[schemas.TemplateResponse])
def update_template(
    template_id: int,
    template_update: schemas.TemplateUpdate,
    db: Session = Depends(get_db)
):
    """Update template and create new version"""
    db_template = db.query(models.Template).filter(models.Template.id == template_id).first()
    if not db_template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    
    update_data = template_update.dict(exclude_unset=True)
    
    # If body or subject is updated, create a new version
    if "body" in update_data or "subject" in update_data:
        # Get the latest version number
        latest_version = db.query(func.max(models.TemplateVersion.version)).filter(
            models.TemplateVersion.template_id == template_id
        ).scalar() or 0
        
        new_version = models.TemplateVersion(
            template_id=template_id,
            version=latest_version + 1,
            subject=update_data.get("subject", db_template.subject),
            body=update_data.get("body", db_template.body),
            variables=update_data.get("variables", db_template.variables)
        )
        db.add(new_version)
        logger.info(f"Created new version {latest_version + 1} for template {template_id}")
    
    # Update template
    for field, value in update_data.items():
        setattr(db_template, field, value)
    
    db.commit()
    db.refresh(db_template)
    
    logger.info(f"Template updated: {db_template.name}")
    return schemas.APIResponse(data=db_template, message="Template updated successfully")

@router.delete("/{template_id}", response_model=schemas.APIResponse)
def delete_template(template_id: int, db: Session = Depends(get_db)):
    """Delete template"""
    db_template = db.query(models.Template).filter(models.Template.id == template_id).first()
    if not db_template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    
    db.delete(db_template)
    db.commit()
    
    logger.info(f"Template deleted: {db_template.name}")
    return schemas.APIResponse(message="Template deleted successfully")

@router.get("/{template_id}/versions", response_model=schemas.APIResponse[List[schemas.TemplateVersionResponse]])
def get_template_versions(template_id: int, db: Session = Depends(get_db)):
    """Get all versions of a template"""
    template = db.query(models.Template).filter(models.Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    
    versions = db.query(models.TemplateVersion).filter(
        models.TemplateVersion.template_id == template_id
    ).order_by(desc(models.TemplateVersion.version)).all()
    
    return schemas.APIResponse(
        data=versions,
        message="Template versions retrieved successfully"
    )

@router.post("/render", response_model=schemas.APIResponse[schemas.TemplateRenderResponse])
def render_template_endpoint(request: schemas.TemplateRenderRequest, db: Session = Depends(get_db)):
    """Render a template with provided variables"""
    logger.info(f"Rendering template: {request.template_name}")
    
    # Get template
    template = db.query(models.Template).filter(
        models.Template.name == request.template_name,
        models.Template.language == request.language,
        models.Template.is_active == True
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Active template '{request.template_name}' not found for language '{request.language}'"
        )
    
    try:
        # Render template
        rendered_body = render_template(template.body, request.variables)
        rendered_subject = render_template(template.subject, request.variables) if template.subject else None
        
        return schemas.APIResponse(
            data=schemas.TemplateRenderResponse(
                subject=rendered_subject,
                body=rendered_body,
                rendered=True
            ),
            message="Template rendered successfully"
        )
    except Exception as e:
        logger.error(f"Error rendering template: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error rendering template: {str(e)}"
        )
